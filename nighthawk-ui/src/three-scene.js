import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const instances = new Map();
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const valueColor = (value) => {
  const t = clamp((Number(value) + 100) / 50, 0, 1);
  const stops = [
    [0.00, [0.72, 0.30, 0.46]],
    [0.30, [0.88, 0.55, 0.36]],
    [0.58, [0.83, 0.80, 0.39]],
    [1.00, [0.30, 0.82, 0.61]]
  ];
  let left = stops[0], right = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (t >= stops[i][0] && t <= stops[i + 1][0]) {
      left = stops[i]; right = stops[i + 1]; break;
    }
  }
  const f = (t - left[0]) / Math.max(1e-6, right[0] - left[0]);
  return left[1].map((v, i) => v + (right[1][i] - v) * f);
};

function getInstance(elementId) {
  const host = document.getElementById(elementId);
  if (!host) return null;
  let instance = instances.get(elementId);
  if (instance && instance.host !== host) {
    instance.dispose();
    instances.delete(elementId);
    instance = null;
  }
  if (instance) return instance;
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
  } catch (error) {
    host.innerHTML = '<div class="webgl-fallback">WebGL is unavailable in this browser or graphics driver. Update the browser/GPU driver and enable hardware acceleration.</div>';
    console.warn("NightHawk WebGL renderer unavailable", error);
    return null;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(Math.max(host.clientWidth, 320), Math.max(host.clientHeight, 260), false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.innerHTML = "";
  host.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#0a1321");
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1000);
  camera.position.set(13, 12, 15);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.maxPolarAngle = Math.PI * 0.48;
  controls.minDistance = 3;
  controls.maxDistance = 90;
  scene.add(new THREE.HemisphereLight(0xb8d9ff, 0x172033, 2.0));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(8, 16, 10);
  key.castShadow = true;
  scene.add(key);
  const grid = new THREE.GridHelper(40, 40, 0x35546b, 0x1d3144);
  grid.position.y = -0.015;
  scene.add(grid);
  const root = new THREE.Group();
  scene.add(root);
  let resizeObserver = null;
  if (typeof ResizeObserver !== "undefined") {
    resizeObserver = new ResizeObserver(() => resize());
    resizeObserver.observe(host);
  }
  function resize() {
    const width = Math.max(host.clientWidth, 320);
    const height = Math.max(host.clientHeight, 260);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
  function animate() {
    controls.update();
    renderer.render(scene, camera);
  }
  renderer.setAnimationLoop(animate);
  instance = {
    host, renderer, scene, camera, controls, root,
    resize,
    dispose() {
      renderer.setAnimationLoop(null);
      resizeObserver?.disconnect();
      controls.dispose();
      root.traverse(obj => {
        obj.geometry?.dispose?.();
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material?.dispose?.();
      });
      renderer.dispose();
      renderer.domElement.remove();
    }
  };
  instances.set(elementId, instance);
  return instance;
}

function clearRoot(root) {
  const children = [...root.children];
  for (const child of children) {
    root.remove(child);
    child.traverse(obj => {
      obj.geometry?.dispose?.();
      if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
      else obj.material?.dispose?.();
    });
  }
}

function addRouter(root, x, z, y = 0.2) {
  const marker = new THREE.Group();
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.72, 0.18, 0.5),
    new THREE.MeshStandardMaterial({ color: 0x66e2df, metalness: 0.35, roughness: 0.3 })
  );
  body.position.y = y;
  body.castShadow = true;
  marker.add(body);
  const pole = new THREE.Mesh(
    new THREE.CylinderGeometry(0.025, 0.025, 0.42, 8),
    new THREE.MeshStandardMaterial({ color: 0xd8ffff })
  );
  pole.position.set(0, y + 0.28, 0);
  marker.add(pole);
  marker.position.set(x, 0, z);
  root.add(marker);
}

export function renderHomeScene(elementId, project, surveyPoints = [], angleDegrees = 0) {
  const instance = getInstance(elementId);
  if (!instance) return false;
  const { root, camera, controls } = instance;
  clearRoot(root);
  const width = Number(project.width_m) || 10;
  const depth = Number(project.height_m) || 8;
  const wallHeight = Number(project.wall_height_m) || 2.7;
  const ox = -width / 2, oz = -depth / 2;
  const floor = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.12, depth),
    new THREE.MeshStandardMaterial({ color: 0x14283a, roughness: 0.88 })
  );
  floor.position.set(0, -0.06, 0);
  floor.receiveShadow = true;
  root.add(floor);
  const grid = new THREE.GridHelper(Math.max(width, depth), Math.max(2, Math.ceil(Math.max(width, depth))), 0x537087, 0x284157);
  grid.position.y = 0.005;
  root.add(grid);

  for (const wall of project.walls || []) {
    const x1 = Number(wall.x1), z1 = Number(wall.y1);
    const x2 = Number(wall.x2), z2 = Number(wall.y2);
    const length = Math.hypot(x2 - x1, z2 - z1);
    if (!Number.isFinite(length) || length < 0.05) continue;
    const color = ({ drywall: 0x8cabc1, wood: 0xc79c65, glass: 0x74cad6, brick: 0xcf806d, concrete: 0xa5aebb, metal: 0xa18ddd })[wall.material] || 0x8cabc1;
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(length, wallHeight, 0.12),
      new THREE.MeshStandardMaterial({ color, roughness: 0.7, transparent: wall.material === "glass", opacity: wall.material === "glass" ? 0.48 : 1 })
    );
    mesh.position.set((x1 + x2) / 2 + ox, wallHeight / 2, (z1 + z2) / 2 + oz);
    mesh.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    root.add(mesh);
  }

  const routerX = Number(project.router?.x ?? width / 2);
  const routerZ = Number(project.router?.y ?? depth / 2);
  addRouter(root, routerX + ox, routerZ + oz, 0.16);
  for (const point of surveyPoints || []) {
    const value = Number(point.rssi_dbm);
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(0.095, 12, 10),
      new THREE.MeshStandardMaterial({ color: new THREE.Color(...valueColor(value)), emissive: new THREE.Color(...valueColor(value)), emissiveIntensity: 0.22 })
    );
    dot.position.set(Number(point.x) + ox, 0.16, Number(point.y) + oz);
    root.add(dot);
  }
  controls.target.set(0, wallHeight * 0.28, 0);
  const radius = Math.max(width, depth) * 1.55 + wallHeight;
  const angle = Number(angleDegrees || 0) * Math.PI / 180 + Math.PI / 4;
  camera.position.set(Math.sin(angle) * radius, radius * 0.78, Math.cos(angle) * radius);
  controls.update();
  instance.resize();
  return true;
}

export function renderCoverageSurface(elementId, data, project, angleDegrees = 0) {
  const instance = getInstance(elementId);
  if (!instance) return false;
  const { root, camera, controls } = instance;
  clearRoot(root);
  const xs = data?.xs || [], ys = data?.ys || [], rows = data?.values || [];
  if (xs.length < 2 || ys.length < 2 || rows.length !== ys.length) return false;
  const nx = xs.length, ny = ys.length;
  const min = Number.isFinite(data.min_dbm) ? data.min_dbm : -100;
  const max = Number.isFinite(data.max_dbm) ? data.max_dbm : -50;
  const vertices = [], colors = [], indices = [];
  for (let j = 0; j < ny; j++) {
    if (!Array.isArray(rows[j]) || rows[j].length !== nx) return false;
    for (let i = 0; i < nx; i++) {
      const value = rows[j][i] == null ? min : Number(rows[j][i]);
      const x = Number(xs[i]) - Number(data.width_m) / 2;
      const z = Number(ys[j]) - Number(data.height_m) / 2;
      const normalized = clamp((value - min) / Math.max(1, max - min), 0, 1);
      const elevation = 0.12 + normalized * 2.4;
      vertices.push(x, elevation, z);
      colors.push(...valueColor(value));
      if (i < nx - 1 && j < ny - 1) {
        const a = j * nx + i, b = a + 1, c = a + nx, d = c + 1;
        indices.push(a, c, b, b, c, d);
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  const surface = new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: 0.64, metalness: 0.05 })
  );
  surface.castShadow = true;
  surface.receiveShadow = true;
  root.add(surface);
  const base = new THREE.Mesh(
    new THREE.PlaneGeometry(Number(data.width_m), Number(data.height_m)),
    new THREE.MeshStandardMaterial({ color: 0x12283a, side: THREE.DoubleSide, transparent: true, opacity: 0.55 })
  );
  base.rotation.x = -Math.PI / 2;
  base.position.y = -0.02;
  root.add(base);
  const grid = new THREE.GridHelper(Math.max(Number(data.width_m), Number(data.height_m)), 20, 0x55748a, 0x284057);
  grid.position.y = 0;
  root.add(grid);
  if (project?.router) {
    addRouter(root, Number(project.router.x) - Number(data.width_m) / 2, Number(project.router.y) - Number(data.height_m) / 2, 0.15);
  }
  controls.target.set(0, 0.75, 0);
  const radius = Math.max(Number(data.width_m), Number(data.height_m)) * 1.6;
  const angle = Number(angleDegrees || 0) * Math.PI / 180 + Math.PI / 4;
  camera.position.set(Math.sin(angle) * radius, radius * 0.92, Math.cos(angle) * radius);
  controls.update();
  instance.resize();
  return true;
}

export function disposeScene(elementId) {
  const instance = instances.get(elementId);
  if (!instance) return;
  instance.dispose();
  instances.delete(elementId);
}
