const $ = (id) => document.getElementById(id);
const state = { project:null, sessions:[], points:[], networks:[], selectedPoint:null, activeSession:null, activeFloorId:"floor_1", coverage:null, coveragePoints:[], coverageKind:"predicted", wallStart:null, mode:"select", scan:null, volumetricPoints:[], csiTimer:null, devices:[], interfaces:[], history:[], selectedHistoryIds:new Set(), channelData:null };
const titles = {overview:"Overview",scanner:"Wi-Fi Scanner",network:"Network & Devices",channels:"Channel Spectrum",history:"Scan History",survey:"Home Survey",floorplan:"Floor Plan & 3D",coverage:"Coverage Maps",csi:"CSI Sensing",volumetric:"Volumetric Data"};
const api = async (path, options={}) => {
  const response = await fetch(path,{headers:{"Content-Type":"application/json",...(options.headers||{})},...options});
  const text = await response.text(); let data={};
  try{data=text?JSON.parse(text):{}}catch{data={detail:text}}
  if(!response.ok) throw new Error(data.detail||data.message||("HTTP "+response.status));
  return data;
};
function toast(message,error=false){const el=$("toast");el.textContent=message;el.className="toast show"+(error?" error":"");clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.className="toast",3200)}
function dbmColor(v){if(v==null)return "#26364d";if(v>=-55)return "#54d49b";if(v>=-70)return "#d4cc68";if(v>=-85)return "#df9465";return "#ba5e78"}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function activeFloor(){return state.project?.floors?.find(f=>f.id===state.activeFloorId)||state.project?.floors?.[0]||null}
function ensureFloorModel(project){
  if(!Array.isArray(project.floors)||!project.floors.length){
    project.floors=[{id:"floor_1",name:"Ground floor",elevation_m:0,width_m:project.width_m,height_m:project.height_m,wall_height_m:project.wall_height_m,floor_loss_db:18,walls:project.walls||[]}];
  }
  project.router_floor_id=project.router_floor_id||project.floors[0].id;
  if(!project.floors.some(f=>f.id===state.activeFloorId))state.activeFloorId=project.active_floor_id||project.floors[0].id;
  const floor=activeFloor();project.width_m=floor.width_m;project.height_m=floor.height_m;project.wall_height_m=floor.wall_height_m;project.walls=floor.walls||[];
}
function syncFloorFromForm(){
  const floor=activeFloor();if(!floor)return;
  floor.width_m=Number($("planWidth").value)||floor.width_m;
  floor.height_m=Number($("planHeight").value)||floor.height_m;
  floor.wall_height_m=Number($("wallHeight").value)||floor.wall_height_m;
  floor.walls=state.project.walls;
}
function refreshFloorSelectors(){
  const options=(state.project?.floors||[]).map(f=>'<option value="'+esc(f.id)+'">'+esc(f.name)+' · '+Number(f.elevation_m).toFixed(1)+' m</option>').join("");
  $("activeFloor").innerHTML=options;$("surveyFloor").innerHTML=options;
  $("activeFloor").value=state.activeFloorId;$("surveyFloor").value=state.activeFloorId;
}
function activateFloor(id,saveCurrent=true){
  if(saveCurrent)syncFloorFromForm();
  if(!state.project?.floors?.some(f=>f.id===id))return;
  state.activeFloorId=id;const floor=activeFloor(),p=state.project;
  p.width_m=floor.width_m;p.height_m=floor.height_m;p.wall_height_m=floor.wall_height_m;p.walls=floor.walls||[];
  $("planWidth").value=floor.width_m;$("planHeight").value=floor.height_m;$("wallHeight").value=floor.wall_height_m;
  refreshFloorSelectors();renderWallList();drawAllPlans();
  $("planDimensions").textContent=floor.width_m+" × "+floor.height_m+" m";
  $("savedLabel").textContent="FLOOR SELECTED";
}
function showView(name){
  document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id==="view-"+name));
  document.querySelectorAll(".nav-item").forEach(v=>v.classList.toggle("active",v.dataset.view===name));
  $("pageTitle").textContent=titles[name]||name;
  if(name==="network")loadNetworkData().catch(e=>toast(e.message,true));
  if(name==="channels")loadChannelData().catch(e=>toast(e.message,true));
  if(name==="history")loadHistoryData().catch(e=>toast(e.message,true));
  if(name==="survey")drawPlan($("surveyCanvas"),true);
  if(name==="floorplan")drawAllPlans();
  if(name==="coverage"&&state.coverage){drawHeat();drawCoverage3D();}
  if(name==="csi"){refreshCsiPorts().catch(e=>toast(e.message,true));refreshCsiStatus().catch(()=>{});startCsiPolling()}
  if(name==="volumetric")loadVolumetric().catch(e=>toast(e.message,true));
  if(name==="overview")refreshStats()
}
document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>showView(b.dataset.view)));
document.querySelectorAll("[data-go]").forEach(b=>b.addEventListener("click",()=>showView(b.dataset.go)));
window.addEventListener("resize",()=>{drawAllPlans();if(state.coverage){drawHeat();drawCoverage3D()}});
async function boot(){
  try{
    const [health,project,sessions]=await Promise.all([api("/api/health"),api("/api/project"),api("/api/surveys")]);
    state.project=project;state.sessions=sessions;ensureFloorModel(project);
    $("apiStatus").innerHTML="<i></i> LOCAL API ONLINE";$("apiStatus").classList.remove("offline");
    $("apiDetail").textContent="Local service responding · "+health.version;$("apiBadge").textContent="ONLINE";
    $("dataLocation").textContent="SQLite · "+health.data_directory;
    fillProjectForm();fillSessions();refreshStats();drawAllPlans();
  }catch(e){$("apiStatus").innerHTML="<i></i> API OFFLINE";$("apiStatus").classList.add("offline");$("apiDetail").textContent=e.message;$("apiBadge").textContent="OFFLINE";toast("Could not connect to NightHawk API: "+e.message,true)}
}
async function refreshStats(){
  $("statPoints").textContent=state.sessions.reduce((n,s)=>n+s.point_count,0);
  $("statSessions").textContent=state.sessions.length;
  if(state.project){const p=state.project;$("statArea").textContent=(p.width_m*p.height_m).toFixed(1)+" m²";$("statPlan").textContent=p.name+" · "+p.width_m+" × "+p.height_m+" m"}
  $("statAps").textContent=state.scan?state.networks.length:"—";$("statApsNote").textContent=state.scan?"Last scan completed":"Run a Wi-Fi scan";
  $("networkCount").textContent=state.scan?state.networks.length:"—";
}
async function refreshAll(){await boot();if(state.activeSession)await loadPoints(state.activeSession)}
$("refreshAll").addEventListener("click",refreshAll);
function signalHtml(n){const p=n.signal_percent??0;return '<span class="signal-track"><i style="width:'+p+'%"></i></span>'+p+'%'}
async function scanWifi(){
  $("scanButton").disabled=true;$("scanButton").textContent="Scanning…";
  try{
    const data=await api("/api/wifi/scan");state.scan=data;state.networks=data.networks||[];
    $("connectedSsid").textContent=data.connected.ssid||"Not connected";
    $("connectedSignal").textContent=data.connected.signal_percent==null?"No active connection":"Signal "+data.connected.signal_percent+"% · est. "+(data.connected.rssi_dbm_estimate??"—")+" dBm";
    $("scanTime").textContent="Scanned "+new Date(data.scanned_at).toLocaleTimeString();
    $("networkCount").textContent=state.networks.length;
    $("networkRows").innerHTML=state.networks.length?state.networks.map(n=>'<tr><td><strong>'+esc(n.ssid||"(Hidden network)")+'</strong>'+(n.is_connected?' <span class="status-tag">CONNECTED</span>':'')+'</td><td class="muted">'+esc(n.bssid)+'</td><td>'+signalHtml(n)+'<small class="muted"> est. '+(n.rssi_dbm_estimate??"—")+' dBm</small></td><td>'+esc(n.channel??"—")+'</td><td>'+esc(n.band)+'</td><td>'+esc(n.authentication||"—")+'</td></tr>').join(""):'<tr><td colspan="6" class="empty">No access points returned. Check that Wi-Fi is enabled and try again.</td></tr>';
    $("wifiDetail").textContent=state.networks.length+" access points visible";$("wifiBadge").textContent="SCANNED";$("wifiDot").className="status-dot green";$("statAps").textContent=state.networks.length;$("statApsNote").textContent="Last scan completed";
    $("networkSelect").innerHTML='<option value="">Choose a detected network</option>'+state.networks.map((n,i)=>'<option value="'+i+'">'+esc(n.ssid||n.bssid)+' · '+(n.rssi_dbm_estimate??"—")+' dBm est.</option>').join("");
    toast("Wi-Fi scan complete: "+state.networks.length+" access points");
  }catch(e){$("wifiDetail").textContent=e.message;$("wifiBadge").textContent="UNAVAILABLE";$("wifiDot").className="status-dot amber";toast(e.message,true)}
  finally{$("scanButton").disabled=false;$("scanButton").textContent="↻ Scan now"}
}
$("scanButton").addEventListener("click",scanWifi);
function fillSessions(){
  const options=state.sessions.map(s=>'<option value="'+s.id+'">'+esc(s.name)+' ('+s.point_count+' pts)</option>').join("");
  $("sessionSelect").innerHTML='<option value="">Choose a survey session</option>'+options;
  $("coverageSession").innerHTML='<option value="">Choose survey</option>'+options;
  if(state.activeSession&&state.sessions.some(s=>s.id===state.activeSession))$("sessionSelect").value=state.activeSession;
}
async function newSurvey(){
  const name=prompt("Name this survey session","Living room survey");if(name===null)return;
  try{const session=await api("/api/surveys",{method:"POST",body:JSON.stringify({name:name.trim()||"Home survey"})});state.sessions.unshift(session);state.activeSession=session.id;fillSessions();$("sessionSelect").value=session.id;await loadPoints(session.id);toast("Survey session created")}
  catch(e){toast(e.message,true)}
}
$("newSurvey").addEventListener("click",newSurvey);
$("sessionSelect").addEventListener("change",async e=>{state.activeSession=e.target.value?Number(e.target.value):null;await loadPoints(state.activeSession)});
async function loadPoints(id){
  state.points=id?await api("/api/surveys/"+id+"/points"):[];
  $("sessionPointCount").innerHTML=state.points.length+' <small>points</small>';
  $("recentPoints").innerHTML=state.points.length?state.points.slice().reverse().slice(0,12).map(p=>'<div class="point-item"><span>('+p.x.toFixed(1)+', '+p.y.toFixed(1)+') m</span><b>'+p.rssi_dbm+' dBm</b></div>').join(""):'<div class="empty">No measurements in this session yet.</div>';
  $("exportCsv").disabled=!id||!state.points.length;$("capturePoint").disabled=!id||!state.selectedPoint;
  fillSessions();refreshStats();drawPlan($("surveyCanvas"),true);
}
$("networkSelect").addEventListener("change",()=>{
  const n=state.networks[Number($("networkSelect").value)];
  if(n&&n.rssi_dbm_estimate!=null){$("manualRssi").value=n.rssi_dbm_estimate;$("manualRssi").dataset.source="estimate"}
  else if(!$("manualRssi").dataset.source||$("manualRssi").dataset.source==="estimate"){$("manualRssi").value="";$("manualRssi").dataset.source=""}
  $("capturePoint").disabled=!state.activeSession||!state.selectedPoint||$("manualRssi").value==="";
});
$("manualRssi").addEventListener("input",()=>{
  $("manualRssi").dataset.source="manual";
  $("capturePoint").disabled=!state.activeSession||!state.selectedPoint||$("manualRssi").value==="";
});
$("capturePoint").addEventListener("click",async()=>{
  if(!state.activeSession||!state.selectedPoint)return;
  const n=state.networks[Number($("networkSelect").value)]||{};
  const chosen=$("manualRssi").value!==""?Number($("manualRssi").value):n.rssi_dbm_estimate;
  if(!Number.isFinite(chosen)){toast("Select a scanned network or enter RSSI manually",true);return}
  const payload={...state.selectedPoint,floor_id:state.activeFloorId,rssi_dbm:chosen,ssid:n.ssid||"",bssid:n.bssid||"",signal_percent:n.signal_percent??null,measurement_source:$("manualRssi").dataset.source==="manual"?"manual":"windows_netsh_signal_estimate"};
  try{await api("/api/surveys/"+state.activeSession+"/points",{method:"POST",body:JSON.stringify(payload)});await loadPoints(state.activeSession);toast("Measurement saved locally")}
  catch(e){toast(e.message,true)}
});
$("exportCsv").addEventListener("click",()=>{if(state.activeSession)window.location.href="/api/surveys/"+state.activeSession+"/export.csv"});
function fillProjectForm(){
  const p=state.project;if(!p)return;ensureFloorModel(p);const floor=activeFloor();
  p.width_m=floor.width_m;p.height_m=floor.height_m;p.wall_height_m=floor.wall_height_m;p.walls=floor.walls||[];
  $("projectName").value=p.name;$("planWidth").value=floor.width_m;$("planHeight").value=floor.height_m;$("wallHeight").value=floor.wall_height_m;
  $("frequency").value=p.frequency_mhz;$("txPower").value=p.tx_power_dbm;$("routerX").value=p.router.x;$("routerY").value=p.router.y;
  refreshFloorSelectors();renderWallList();
}
function projectFromForm(){
  const p=state.project;syncFloorFromForm();
  p.name=$("projectName").value||"My Home";p.width_m=Number($("planWidth").value);p.height_m=Number($("planHeight").value);p.wall_height_m=Number($("wallHeight").value);
  p.frequency_mhz=Number($("frequency").value);p.tx_power_dbm=Number($("txPower").value);
  p.router={...p.router,x:Number($("routerX").value),y:Number($("routerY").value)};
  return {...p,floors:p.floors.map(f=>({...f,walls:f.walls||[]}))};
}
$("activeFloor").addEventListener("change",e=>activateFloor(e.target.value,true));
$("surveyFloor").addEventListener("change",e=>activateFloor(e.target.value,true));
$("addFloor").addEventListener("click",()=>{
  syncFloorFromForm();
  const name=prompt("New floor name","First floor");if(name===null)return;
  const current=activeFloor(),id="floor_"+(state.project.floors.length+1);
  const elevation=Math.max(...state.project.floors.map(f=>Number(f.elevation_m)))+3.2;
  state.project.floors.push({id,name:name.trim()||"New floor",elevation_m:elevation,width_m:current.width_m,height_m:current.height_m,wall_height_m:current.wall_height_m,floor_loss_db:18,walls:[]});
  activateFloor(id,false);toast("Floor added. Draw its internal walls and save the project.");
});
async function saveProject(){
  try{const p=projectFromForm();const saved=await api("/api/project",{method:"PUT",body:JSON.stringify(p)});state.project=saved;fillProjectForm();$("savedLabel").textContent="SAVED · "+new Date().toLocaleTimeString();drawAllPlans();refreshStats();toast("Floor plan saved to local SQLite")}
  catch(e){toast(e.message,true)}
}
$("saveProject").addEventListener("click",saveProject);
$("exportProject").addEventListener("click",()=>{window.location.href="/api/project/export.json"});
$("importProject").addEventListener("click",()=>$("projectFile").click());
$("projectFile").addEventListener("change",async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{
    const imported=JSON.parse(await file.text());
    const saved=await api("/api/project/import",{method:"POST",body:JSON.stringify(imported)});
    state.project=saved;fillProjectForm();drawAllPlans();refreshStats();
    toast("Project imported and saved locally");
  }catch(err){toast("Project import failed: "+err.message,true)}
  finally{e.target.value=""}
});
$("optimizeRouter").addEventListener("click",async()=>{
  $("optimizeRouter").disabled=true;$("optimizeRouter").textContent="Calculating…";
  try{
    const result=await api("/api/router/optimize?step_m=1&resolution=10&floor_id="+encodeURIComponent(state.activeFloorId));
    const best=result.best;
    if(!best)throw new Error("No candidate router position found");
    $("routerX").value=best.x;$("routerY").value=best.y;
    state.project.router.x=best.x;state.project.router.y=best.y;state.project.router_floor_id=state.activeFloorId;
    $("optimizerResult").textContent="Suggested: "+best.x+" m, "+best.y+" m · model mean "+best.mean_rssi_dbm+" dBm · Save to apply.";
    $("savedLabel").textContent="UNSAVED CHANGES";drawAllPlans();
    toast("Best modelled position found. Review and save it.");
  }catch(e){toast(e.message,true)}
  finally{$("optimizeRouter").disabled=false;$("optimizeRouter").textContent="✦ Find better router position"}
});
function renderWallList(){$("wallList").innerHTML=(state.project?.walls||[]).map((w,i)=>'<div class="wall-row"><span>'+(i+1)+'. '+esc(w.material)+' · '+Math.hypot(w.x2-w.x1,w.y2-w.y1).toFixed(1)+' m</span><button data-remove-wall="'+i+'" title="Remove wall">×</button></div>').join("")||'<div class="empty">No internal walls added.</div>';$("wallCount").textContent=(state.project?.walls.length||0)+" walls"}
$("wallList").addEventListener("click",async e=>{const b=e.target.closest("[data-remove-wall]");if(!b)return;state.project.walls.splice(Number(b.dataset.removeWall),1);renderWallList();drawAllPlans();await saveProject()});
$("planMode").addEventListener("change",e=>{state.mode=e.target.value;state.wallStart=null;$("toolHelp").textContent=state.mode==="wall"?"Click two points on the plan to add a wall.":state.mode==="router"?"Click the plan to move the router.":"Choose Draw wall or Place router to edit the plan.";});
$("orbit").addEventListener("input",drawScene);
$("coverageOrbit").addEventListener("input",drawCoverage3D);
function canvasMetrics(canvas,width,height){
  const rect=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);
  const w=Math.max(1,Math.floor(rect.width*dpr)),h=Math.max(1,Math.floor(rect.height*dpr));
  if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}
  const ctx=canvas.getContext("2d");ctx.setTransform(dpr,0,0,dpr,0,0);
  return {ctx,w:rect.width,h:rect.height};
}
function worldToCanvas(x,y,canvas){
  const p=state.project;const rect=canvas.getBoundingClientRect();const pad=26;
  const scale=Math.min((rect.width-pad*2)/p.width_m,(rect.height-pad*2)/p.height_m);
  return {x:(rect.width-p.width_m*scale)/2+x*scale,y:(rect.height+p.height*scale)/2-y*scale,scale};
}
function canvasToWorld(px,py,canvas){
  const p=state.project;const rect=canvas.getBoundingClientRect();const pad=26;
  const scale=Math.min((rect.width-pad*2)/p.width_m,(rect.height-pad*2)/p.height_m);
  const x=(px-(rect.width-p.width_m*scale)/2)/scale;
  const y=(rect.height-(py-(rect.height-p.height*scale)/2))/scale;
  return {x:Number(x.toFixed(2)),y:Number(y.toFixed(2))};
}
function drawPlan(canvas,showPoints=false){
  if(!canvas||!state.project)return;const {ctx,w,h}=canvasMetrics(canvas);const p=state.project;
  ctx.clearRect(0,0,w,h);ctx.fillStyle="#0a1321";ctx.fillRect(0,0,w,h);
  const o=worldToCanvas(0,0,canvas),scale=o.scale,left=o.x,top=o.y-p.height_m*scale;
  ctx.fillStyle="#102337";ctx.fillRect(left,top,p.width_m*scale,p.height_m*scale);
  ctx.strokeStyle="#1e2e42";ctx.lineWidth=1;
  for(let x=0;x<=p.width_m;x++){const q=worldToCanvas(x,0,canvas);ctx.beginPath();ctx.moveTo(q.x,top);ctx.lineTo(q.x,top+p.height_m*scale);ctx.stroke()}
  for(let y=0;y<=p.height_m;y++){const q=worldToCanvas(0,y,canvas);ctx.beginPath();ctx.moveTo(left,q.y);ctx.lineTo(left+p.width_m*scale,q.y);ctx.stroke()}
  ctx.strokeStyle="#628298";ctx.lineWidth=2;ctx.strokeRect(left,top,p.width_m*scale,p.height_m*scale);
  (p.walls||[]).forEach(wall=>{const a=worldToCanvas(wall.x1,wall.y1,canvas),b=worldToCanvas(wall.x2,wall.y2,canvas);ctx.strokeStyle=wallColor(wall.material);ctx.lineWidth=4;ctx.lineCap="round";ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke()});
  if(p.router_floor_id===state.activeFloorId){const r=worldToCanvas(p.router.x,p.router.y,canvas);ctx.fillStyle="#66e2df";ctx.beginPath();ctx.arc(r.x,r.y,7,0,Math.PI*2);ctx.fill();ctx.strokeStyle="#66e2df55";ctx.lineWidth=8;ctx.beginPath();ctx.arc(r.x,r.y,13,0,Math.PI*2);ctx.stroke();ctx.fillStyle="#b9f6ef";ctx.font="10px Manrope";ctx.fillText("ROUTER",r.x+12,r.y-10)}
  if(showPoints)state.points.filter(point=>point.floor_id===state.activeFloorId).forEach(point=>{const q=worldToCanvas(point.x,point.y,canvas);ctx.fillStyle=dbmColor(point.rssi_dbm);ctx.strokeStyle="#07111d";ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(q.x,q.y,5,0,Math.PI*2);ctx.fill();ctx.stroke()});
  if(state.selectedPoint&&canvas.id==="surveyCanvas"){const q=worldToCanvas(state.selectedPoint.x,state.selectedPoint.y,canvas);ctx.strokeStyle="#fff";ctx.setLineDash([4,3]);ctx.beginPath();ctx.arc(q.x,q.y,9,0,Math.PI*2);ctx.stroke();ctx.setLineDash([])}
}
function wallColor(m){return ({drywall:"#8cabc1",wood:"#c79c65",glass:"#74cad6",brick:"#cf806d",concrete:"#a5aebb",metal:"#a18ddd"})[m]||"#8cabc1"}
function drawAllPlans(){drawPlan($("planCanvas"));drawPlan($("surveyCanvas"),true);drawScene();renderWallList();if(state.project){$("planDimensions").textContent=state.project.width_m+" × "+state.project.height_m+" m"}}
function handlePlanClick(canvas,e,mode){
  if(!state.project)return;const rect=canvas.getBoundingClientRect();const pos=canvasToWorld(e.clientX-rect.left,e.clientY-rect.top,canvas);const p=state.project;
  if(pos.x<0||pos.y<0||pos.x>p.width_m||pos.y>p.height_m)return;
  if(mode==="survey"){state.selectedPoint=pos;$("selectedCoord").textContent=pos.x+" m, "+pos.y+" m";$("capturePoint").disabled=!state.activeSession||$("manualRssi").value==="";drawPlan(canvas,true);return}
  if(mode==="router"){p.router.x=pos.x;p.router.y=pos.y;p.router_floor_id=state.activeFloorId;$("routerX").value=pos.x;$("routerY").value=pos.y;drawAllPlans();$("savedLabel").textContent="UNSAVED CHANGES";return}
  if(mode==="wall"){
    if(!state.wallStart){state.wallStart=pos;$("toolHelp").textContent="First point set. Click the second point.";return}
    if(Math.hypot(pos.x-state.wallStart.x,pos.y-state.wallStart.y)<0.05){toast("Wall is too short",true);return}
    p.walls.push({x1:state.wallStart.x,y1:state.wallStart.y,x2:pos.x,y2:pos.y,material:$("wallMaterial").value});state.wallStart=null;$("toolHelp").textContent="Wall added. Click two more points to continue.";drawAllPlans();$("savedLabel").textContent="UNSAVED CHANGES";return;
  }
}
$("surveyCanvas").addEventListener("click",e=>handlePlanClick($("surveyCanvas"),e,"survey"));
$("planCanvas").addEventListener("click",e=>handlePlanClick($("planCanvas"),e,state.mode));
function drawScene(){
  if(!state.project||!window.NightHawk3D)return;
  const p={...state.project,active_floor_id:state.activeFloorId,router:state.project.router_floor_id===state.activeFloorId?state.project.router:null};
  const points=state.points.filter(point=>point.floor_id===state.activeFloorId);
  window.NightHawk3D.renderHomeScene("sceneCanvas",p,points,Number($("orbit").value||0));
}
async function loadCoverage(kind){
  const session=Number($("coverageSession").value||state.activeSession||0);
  if(kind==="measured"&&!session){toast("Choose a survey session first",true);return}
  try{
    const floorParam="&floor_id="+encodeURIComponent(state.activeFloorId);
    const data=kind==="measured"?await api("/api/coverage/measured?session_id="+session+"&resolution=40"+floorParam):await api("/api/coverage/predicted?resolution=40"+floorParam);
    state.coverage=data;state.coverageKind=kind;
    state.coveragePoints=kind==="measured"?(await api("/api/surveys/"+session+"/points")).filter(p=>p.floor_id===state.activeFloorId):[];
    $("coverageTitle").textContent=(kind==="measured"?"Measured signal heatmap":"Theoretical RF propagation model")+" · "+(activeFloor()?.name||state.activeFloorId);
    $("coverageSubtitle").textContent=kind==="measured"?"IDW interpolation of "+data.point_count+" saved physical readings.":"Estimated from router position, frequency, distance and wall crossings.";
    $("coverageType").textContent=kind==="measured"?"MEASURED · IDW":"MODEL · ESTIMATE";
    $("coverageRange").textContent=data.min_dbm==null?"No data":data.min_dbm+" to "+data.max_dbm+" dBm";
    $("coverageCount").textContent=kind==="measured"?data.point_count+" survey points":"Frequency "+(data.frequency_mhz/1000).toFixed(1)+" GHz";
    drawHeat();drawCoverage3D();toast(kind==="measured"?"Measured coverage calculated":"RF model calculated");
  }catch(e){toast(e.message,true)}
}
$("loadMeasured").addEventListener("click",()=>loadCoverage("measured"));
$("loadPredicted").addEventListener("click",()=>loadCoverage("predicted"));
function drawHeat(){
  const canvas=$("heatCanvas"),d=state.coverage;if(!canvas||!d)return;
  const {ctx,w,h}=canvasMetrics(canvas);ctx.clearRect(0,0,w,h);ctx.fillStyle="#0a1321";ctx.fillRect(0,0,w,h);
  const pad=24,scale=Math.min((w-pad*2)/d.width_m,(h-pad*2)/d.height_m),dw=d.width_m*scale,dh=d.height_m*scale,left=(w-dw)/2,top=(h-dh)/2;
  const rows=d.values,n=rows.length,cellW=dw/n+1,cellH=dh/n+1;
  for(let iy=0;iy<n;iy++)for(let ix=0;ix<n;ix++){const v=rows[iy][ix];if(v==null)continue;ctx.globalAlpha=.82;ctx.fillStyle=dbmColor(v);ctx.fillRect(left+ix*dw/n,top+dh-(iy+1)*dh/n,cellW,cellH)}
  ctx.globalAlpha=1;ctx.strokeStyle="#8ba3b8";ctx.lineWidth=1.5;ctx.strokeRect(left,top,dw,dh);
  const p=state.project;const rx=left+p.router.x/p.width_m*dw,ry=top+dh-p.router.y/p.height_m*dh;ctx.fillStyle="#07131b";ctx.strokeStyle="#e9ffff";ctx.lineWidth=2;ctx.beginPath();ctx.arc(rx,ry,7,0,Math.PI*2);ctx.fill();ctx.stroke();
  if(state.coverageKind==="measured")state.coveragePoints.forEach(pt=>{const x=left+pt.x/p.width_m*dw,y=top+dh-pt.y/p.height_m*dh;ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill()});
}

function drawCoverage3D(){
  if(!state.coverage||!state.project||!window.NightHawk3D)return;
  const p={...state.project,router:state.project.router_floor_id===state.activeFloorId?state.project.router:null};
  window.NightHawk3D.renderCoverageSurface("coverage3dCanvas",state.coverage,p,Number($("coverageOrbit").value||0));
}


async function refreshCsiPorts(){
  const data=await api("/api/csi/ports"),select=$("csiPort"),current=select.value;
  select.innerHTML=data.ports.length?data.ports.map(p=>'<option value="'+esc(p.device)+'">'+esc(p.device+" · "+p.description)+'</option>').join(""):'<option value="">No serial ports found</option>';
  if(data.ports.some(p=>p.device===current))select.value=current;
}
function drawCsiChart(values){
  const canvas=$("csiCanvas");if(!canvas)return;
  const {ctx,w,h}=canvasMetrics(canvas);ctx.clearRect(0,0,w,h);ctx.fillStyle="#0a1321";ctx.fillRect(0,0,w,h);
  if(!values?.length){ctx.fillStyle="#7489a2";ctx.font="12px Consolas";ctx.fillText("Waiting for a valid CSI_DATA serial frame…",18,30);return}
  const max=Math.max(1,...values),gap=3,barW=Math.max(2,(w-36)/values.length-gap);
  ctx.strokeStyle="#22364b";ctx.lineWidth=1;
  for(let i=0;i<5;i++){const y=12+(h-30)*i/4;ctx.beginPath();ctx.moveTo(18,y);ctx.lineTo(w-18,y);ctx.stroke()}
  values.forEach((v,i)=>{const bh=(h-38)*v/max;ctx.fillStyle="#61d4ce";ctx.fillRect(18+i*(barW+gap),h-16-bh,barW,bh)});
  ctx.fillStyle="#8299b1";ctx.font="10px Consolas";ctx.fillText("SUBCARRIER AMPLITUDE",18,12);
}
async function refreshCsiStatus(){
  const status=await api("/api/csi/status");
  $("csiState").textContent=status.state.toUpperCase();$("csiPortLabel").textContent=status.port?status.port+" · "+status.baud+" baud":(status.error||"No device");
  $("csiFrames").textContent=status.frames_received;$("csiSubcarriers").textContent=status.latest?.subcarrier_count??"—";
  $("csiVariance").textContent=status.variance_mean??"—";
  $("csiLiveTag").textContent=status.state==="connected"?"LIVE SERIAL DATA":status.state==="error"?"DEVICE ERROR":"WAITING FOR DEVICE";
  $("connectCsi").disabled=status.state==="connected"||status.state==="connecting";
  $("disconnectCsi").disabled=status.state!=="connected"&&status.state!=="connecting";
  drawCsiChart(status.latest?.amplitudes||[]);
}
function startCsiPolling(){
  if(state.csiTimer)return;
  state.csiTimer=setInterval(()=>{if($("view-csi")?.classList.contains("active"))refreshCsiStatus().catch(e=>console.warn(e))},800);
}
$("refreshCsiPorts").addEventListener("click",()=>refreshCsiPorts().then(()=>toast("Serial ports refreshed")).catch(e=>toast(e.message,true)));
$("connectCsi").addEventListener("click",async()=>{
  try{
    const config={port:$("csiPort").value,baud:Number($("csiBaud").value),csi_column:Number($("csiColumn").value)};
    await api("/api/csi/start",{method:"POST",body:JSON.stringify(config)});
    startCsiPolling();await refreshCsiStatus();toast("CSI serial reader started");
  }catch(e){toast(e.message,true)}
});
$("disconnectCsi").addEventListener("click",async()=>{
  try{await api("/api/csi/stop",{method:"POST",body:"{}"});await refreshCsiStatus();toast("CSI reader stopped")}
  catch(e){toast(e.message,true)}
});
async function loadVolumetric(){
  const data=await api("/api/volumetric/points");state.volumetricPoints=data.points||[];
  $("volumeCount").textContent=data.point_count;
  $("volumeSource").textContent=data.points.length?data.points[0].source_name:"No dataset imported";
  if(data.points.length){const values=data.points.map(p=>p.rssi_dbm);$("volumeRange").textContent=Math.min(...values).toFixed(1)+" to "+Math.max(...values).toFixed(1)}
  else $("volumeRange").textContent="—";
  window.NightHawk3D?.renderVolumetricCloud("volumetricScene",state.volumetricPoints);
}
$("importVolumetric").addEventListener("click",async()=>{
  const file=$("volumetricFile").files?.[0];if(!file){toast("Choose a CSV file first",true);return}
  const button=$("importVolumetric");button.disabled=true;button.textContent="Importing…";
  try{
    const response=await fetch("/api/volumetric/import?filename="+encodeURIComponent(file.name),{method:"POST",headers:{"Content-Type":"text/csv"},body:await file.text()});
    const data=await response.json();if(!response.ok)throw new Error(data.detail||"CSV import failed");
    await loadVolumetric();toast("Imported "+data.point_count+" volumetric measurements");
  }catch(e){toast(e.message,true)}
  finally{button.disabled=false;button.textContent="Import point cloud"}
});
$("reloadVolumetric").addEventListener("click",()=>loadVolumetric().then(()=>toast("Saved point cloud loaded")).catch(e=>toast(e.message,true)));
$("downloadScanPlan").addEventListener("click",()=>{
  const params=new URLSearchParams({
    width_m:$("scanWidth").value,
    depth_m:$("scanDepth").value,
    height_m:$("scanHeight").value,
    step_m:$("scanStep").value
  });
  window.location.href="/api/volumetric/scan-plan.csv?"+params.toString();
});

async function loadSessionDropdowns(){
  state.sessions=await api("/api/surveys");fillSessions();refreshStats();
}
$("coverageSession").addEventListener("change",()=>{});
boot().then(()=>loadSessionDropdowns().catch(()=>{}));

// Network & Devices Controller
async function loadNetworkData() {
  const [netInfo, ifaces, devs] = await Promise.all([
    api("/api/network/info"),
    api("/api/network/interfaces"),
    api("/api/network/devices")
  ]);
  state.interfaces = ifaces || [];
  state.devices = devs || [];

  $("netLocalIp").textContent = netInfo.local_ip || "127.0.0.1";
  $("netSubnet").textContent = "Subnet: " + (netInfo.subnet_mask || "—");
  $("netGateway").textContent = netInfo.default_gateway || "—";
  $("netPing").textContent = netInfo.gateway_ping_ms != null ? ("Latency: " + netInfo.gateway_ping_ms + " ms (" + netInfo.gateway_packet_loss_percent + "% loss)") : "Gateway unreachable";
  $("netDeviceCount").textContent = state.devices.length;
  $("netInternet").textContent = netInfo.internet_reachable ? "Connected" : "No Internet";
  $("netInternet").style.color = netInfo.internet_reachable ? "var(--green)" : "var(--amber)";
  $("netDns").textContent = "DNS: " + (netInfo.dns_servers?.join(", ") || "DHCP");

  $("interfaceRows").innerHTML = state.interfaces.length ? state.interfaces.map(i => `
    <tr>
      <td><strong>${esc(i.name)}</strong>${i.is_connected ? ' <span class="status-tag">CONNECTED</span>' : ''}</td>
      <td class="muted">${esc(i.description)}</td>
      <td><code>${esc(i.physical_address)}</code></td>
      <td><span class="status-tag ${i.is_connected ? '' : 'warning'}">${esc(i.state.toUpperCase())}</span></td>
      <td>${esc(i.radio_type || "—")}</td>
      <td>${i.signal_percent != null ? signalHtml(i) : '—'}<small class="muted"> ${i.rssi_dbm != null ? (i.rssi_dbm + ' dBm') : ''}</small></td>
      <td>${i.receive_rate_mbps ? (i.receive_rate_mbps + ' / ' + i.transmit_rate_mbps + ' Mbps') : '—'}</td>
    </tr>
  `).join("") : '<tr><td colspan="7" class="empty">No wireless interfaces found.</td></tr>';

  renderDevices(state.devices);
}

function renderDevices(devs) {
  $("deviceRows").innerHTML = devs.length ? devs.map(d => `
    <tr>
      <td><strong>${esc(d.ip)}</strong>${d.is_local_host ? ' <span class="status-tag">THIS PC</span>' : (d.is_gateway ? ' <span class="status-tag">ROUTER</span>' : '')}</td>
      <td><code>${esc(d.mac)}</code></td>
      <td>${esc(d.vendor)}</td>
      <td><span class="muted">${esc(d.type.toUpperCase())}</span></td>
      <td><span class="status-tag">ONLINE</span></td>
    </tr>
  `).join("") : '<tr><td colspan="5" class="empty">No matching local network devices.</td></tr>';
}

$("deviceSearch")?.addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();
  if (!query) {
    renderDevices(state.devices);
    return;
  }
  const filtered = state.devices.filter(d => d.ip.includes(query) || d.mac.includes(query) || d.vendor.toLowerCase().includes(query));
  renderDevices(filtered);
});
$("refreshNetworkBtn")?.addEventListener("click", () => loadNetworkData().then(() => toast("Network details updated")).catch(e => toast(e.message, true)));

// Channel Spectrum Controller
async function loadChannelData() {
  const data = await api("/api/network/channels");
  state.channelData = data;
  $("rec2g").textContent = "Channel " + (data.band_2g.recommended_channel || "—");
  $("rec5g").textContent = "Channel " + (data.band_5g.recommended_channel || "—");
  $("total2gCount").textContent = data.band_2g.spectrum.reduce((n, s) => n + s.count, 0);
  $("total5gCount").textContent = data.band_5g.total_5g_networks || 0;
  $("channelTips").textContent = data.tips?.join(" ") || "No tips available.";

  const max2g = Math.max(1, ...data.band_2g.spectrum.map(s => s.count));
  $("chart2g").innerHTML = data.band_2g.spectrum.map(s => {
    const isRec = s.channel === data.band_2g.recommended_channel;
    const isCongested = s.count >= 3;
    const h = Math.max(10, (s.count / max2g) * 120);
    const cls = isRec ? "recommended" : (isCongested ? "congested" : (s.count > 0 ? "active" : ""));
    return `
      <div class="channel-bar-col">
        ${isRec ? '<span class="channel-star">★ BEST</span>' : ''}
        <div class="channel-bar ${cls}" style="height:${h}px">
          ${s.count > 0 ? `<span class="channel-count">${s.count}</span>` : ''}
        </div>
        <span class="channel-label">Ch ${s.channel}${s.is_standard ? '*' : ''}</span>
      </div>
    `;
  }).join("");

  const max5g = Math.max(1, ...(data.band_5g.spectrum.map(s => s.count)));
  $("chart5g").innerHTML = data.band_5g.spectrum.map(s => {
    const isRec = s.channel === data.band_5g.recommended_channel;
    const h = Math.max(10, (s.count / max5g) * 120);
    return `
      <div class="channel-bar-col">
        ${isRec ? '<span class="channel-star">★ BEST</span>' : ''}
        <div class="channel-bar ${isRec ? 'recommended' : (s.count > 0 ? 'active' : '')}" style="height:${h}px">
          ${s.count > 0 ? `<span class="channel-count">${s.count}</span>` : ''}
        </div>
        <span class="channel-label">${s.channel}</span>
      </div>
    `;
  }).join("");
}
$("refreshChannelsBtn")?.addEventListener("click", () => loadChannelData().then(() => toast("Spectrum re-analyzed")).catch(e => toast(e.message, true)));

// Scan History & Comparisons Controller
async function loadHistoryData() {
  const scans = await api("/api/wifi/history");
  state.history = scans || [];
  state.selectedHistoryIds.clear();
  updateCompareButton();
  $("historyPill").textContent = state.history.length + " ARCHIVED SCANS";
  $("historyRows").innerHTML = state.history.length ? state.history.map(s => `
    <tr>
      <td><input type="checkbox" class="history-check" data-id="${s.id}"></td>
      <td><strong>#${s.id}</strong></td>
      <td>${new Date(s.scanned_at).toLocaleString()}</td>
      <td><strong>${esc(s.connected_ssid || "Not connected")}</strong> <small class="muted">${esc(s.connected_bssid)}</small></td>
      <td>${s.network_count} access points</td>
      <td>
        <button class="btn tiny secondary" onclick="viewScanDetails(${s.id})">Inspect</button>
        <button class="btn tiny secondary" style="color:var(--red)" onclick="deleteScanRecord(${s.id})">Delete</button>
      </td>
    </tr>
  `).join("") : '<tr><td colspan="6" class="empty">No past Wi-Fi scans recorded yet. Perform a scan in the Wi-Fi Scanner tab to populate history.</td></tr>';

  document.querySelectorAll(".history-check").forEach(cb => {
    cb.addEventListener("change", (e) => {
      const id = Number(e.target.dataset.id);
      if (e.target.checked) state.selectedHistoryIds.add(id);
      else state.selectedHistoryIds.delete(id);
      updateCompareButton();
    });
  });
}

function updateCompareButton() {
  const btn = $("compareScansBtn");
  if (!btn) return;
  const count = state.selectedHistoryIds.size;
  btn.disabled = count !== 2;
  btn.textContent = count === 2 ? "⇄ Compare Selected (2)" : "⇄ Select 2 Scans to Compare";
}

window.viewScanDetails = async function(id) {
  try {
    const scan = await api("/api/wifi/history/" + id);
    state.scan = scan;
    state.networks = scan.networks || [];
    showView("scanner");
    $("connectedSsid").textContent = scan.connected?.ssid || "Not connected";
    $("connectedSignal").textContent = scan.connected?.signal_percent == null ? "No connection" : ("Signal " + scan.connected.signal_percent + "% · " + (scan.connected.rssi_dbm_estimate ?? "—") + " dBm");
    $("scanTime").textContent = "Archived scan from " + new Date(scan.scanned_at).toLocaleString();
    $("networkCount").textContent = state.networks.length;
    $("networkRows").innerHTML = state.networks.map(n => `
      <tr>
        <td><strong>${esc(n.ssid || "(Hidden)")}</strong>${n.is_connected ? ' <span class="status-tag">CONNECTED</span>' : ''}</td>
        <td class="muted">${esc(n.bssid)}</td>
        <td>${signalHtml(n)}<small class="muted"> est. ${n.rssi_dbm_estimate ?? "—"} dBm</small></td>
        <td>${esc(n.channel ?? "—")}</td>
        <td>${esc(n.band)}</td>
        <td>${esc(n.authentication || "—")}</td>
      </tr>
    `).join("");
    toast("Loaded archived scan #" + id);
  } catch (e) {
    toast(e.message, true);
  }
};

window.deleteScanRecord = async function(id) {
  if (!confirm("Delete archived scan #" + id + "?")) return;
  try {
    await api("/api/wifi/history/" + id, { method: "DELETE" });
    await loadHistoryData();
    toast("Scan #" + id + " deleted");
  } catch (e) {
    toast(e.message, true);
  }
};

$("compareScansBtn")?.addEventListener("click", async () => {
  const ids = Array.from(state.selectedHistoryIds).sort((a, b) => a - b);
  if (ids.length !== 2) return;
  try {
    const diff = await api("/api/wifi/history/compare?baseline_id=" + ids[0] + "&target_id=" + ids[1]);
    $("diffDrawer").classList.remove("hidden");
    $("diffTitle").textContent = "Scan #" + ids[0] + " vs Scan #" + ids[1] + " Delta";
    $("diffSubtitle").textContent = "Baseline: " + new Date(diff.baseline_scan.scanned_at).toLocaleTimeString() + " (" + diff.baseline_scan.network_count + " APs) → Target: " + new Date(diff.target_scan.scanned_at).toLocaleTimeString() + " (" + diff.target_scan.network_count + " APs)";
    $("diffCommon").textContent = diff.summary.common_count;
    $("diffNew").textContent = "+" + diff.summary.new_count;
    $("diffLost").textContent = "-" + diff.summary.lost_count;
    const deltaSign = diff.summary.average_signal_delta_dbm > 0 ? "+" : "";
    $("diffAvgDelta").textContent = deltaSign + diff.summary.average_signal_delta_dbm + " dBm";

    let rows = "";
    diff.persistent_networks.forEach(p => {
      const d = p.delta_rssi_dbm;
      const sign = d > 0 ? "+" : "";
      const badgeCls = d > 0 ? "plus" : (d < 0 ? "minus" : "neutral");
      rows += `
        <tr>
          <td><strong>${esc(p.ssid || "(Hidden)")}</strong></td>
          <td><code>${esc(p.bssid)}</code></td>
          <td>${esc(p.band || "—")}</td>
          <td>${esc(p.channel || "—")}</td>
          <td>${p.baseline_rssi_dbm ?? "—"} dBm</td>
          <td>${p.current_rssi_dbm ?? "—"} dBm</td>
          <td><span class="diff-badge ${badgeCls}">${sign}${d ?? 0} dBm</span></td>
        </tr>
      `;
    });
    diff.new_networks.forEach(n => {
      rows += `
        <tr>
          <td><strong>${esc(n.ssid || "(Hidden)")}</strong> <span class="diff-badge plus">+NEW</span></td>
          <td><code>${esc(n.bssid)}</code></td>
          <td>${esc(n.band || "—")}</td>
          <td>${esc(n.channel || "—")}</td>
          <td>—</td>
          <td>${n.rssi_dbm_estimate ?? "—"} dBm</td>
          <td><span class="diff-badge plus">APPEARED</span></td>
        </tr>
      `;
    });
    diff.lost_networks.forEach(n => {
      rows += `
        <tr>
          <td><strong>${esc(n.ssid || "(Hidden)")}</strong> <span class="diff-badge minus">-LOST</span></td>
          <td><code>${esc(n.bssid)}</code></td>
          <td>${esc(n.band || "—")}</td>
          <td>${esc(n.channel || "—")}</td>
          <td>${n.rssi_dbm_estimate ?? "—"} dBm</td>
          <td>—</td>
          <td><span class="diff-badge minus">DISAPPEARED</span></td>
        </tr>
      `;
    });
    $("diffRows").innerHTML = rows || '<tr><td colspan="7" class="empty">No differences between scans.</td></tr>';
  } catch (e) {
    toast(e.message, true);
  }
});
$("closeDiffBtn")?.addEventListener("click", () => $("diffDrawer").classList.add("hidden"));
$("exportHistoryCsv")?.addEventListener("click", () => window.location.href = "/api/wifi/history/export.csv");
$("exportHistoryJson")?.addEventListener("click", () => window.location.href = "/api/wifi/history/export.json");

// Camera Mode Switcher Controller
document.querySelectorAll("[data-cam]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-cam]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    window.NightHawk3D?.setCameraMode("sceneCanvas", btn.dataset.cam);
    toast("Camera view: " + btn.textContent);
  });
});

