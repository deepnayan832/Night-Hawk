const $ = (id) => document.getElementById(id);
const state = { project:null, sessions:[], points:[], networks:[], selectedPoint:null, activeSession:null, coverage:null, coverageKind:"predicted", wallStart:null, mode:"select", scan:null };
const titles = {overview:"Overview",scanner:"Wi-Fi Scanner",survey:"Home Survey",floorplan:"Floor Plan & 3D",coverage:"Coverage Maps"};
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
function showView(name){document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id==="view-"+name));document.querySelectorAll(".nav-item").forEach(v=>v.classList.toggle("active",v.dataset.view===name));$("pageTitle").textContent=titles[name];if(name==="survey")drawPlan($("surveyCanvas"),true);if(name==="floorplan")drawAllPlans();if(name==="coverage"&&state.coverage)drawHeat();if(name==="overview")refreshStats()}
document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>showView(b.dataset.view)));
document.querySelectorAll("[data-go]").forEach(b=>b.addEventListener("click",()=>showView(b.dataset.go)));
window.addEventListener("resize",()=>{drawAllPlans();if(state.coverage)drawHeat()});
async function boot(){
  try{
    const [health,project,sessions]=await Promise.all([api("/api/health"),api("/api/project"),api("/api/surveys")]);
    state.project=project;state.sessions=sessions;
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
$("networkSelect").addEventListener("change",()=>{const n=state.networks[Number($("networkSelect").value)];if(n&&n.rssi_dbm_estimate!=null)$("manualRssi").value=n.rssi_dbm_estimate});
$("manualRssi").addEventListener("input",()=>{$("capturePoint").disabled=!state.activeSession||!state.selectedPoint||$("manualRssi").value===""});
$("capturePoint").addEventListener("click",async()=>{
  if(!state.activeSession||!state.selectedPoint)return;
  const n=state.networks[Number($("networkSelect").value)]||{};
  const chosen=$("manualRssi").value!==""?Number($("manualRssi").value):n.rssi_dbm_estimate;
  if(!Number.isFinite(chosen)){toast("Select a scanned network or enter RSSI manually",true);return}
  const payload={...state.selectedPoint,rssi_dbm:chosen,ssid:n.ssid||"",bssid:n.bssid||"",signal_percent:n.signal_percent??null,measurement_source:$("manualRssi").value!==""?"manual":"windows_netsh_signal_estimate"};
  try{await api("/api/surveys/"+state.activeSession+"/points",{method:"POST",body:JSON.stringify(payload)});await loadPoints(state.activeSession);toast("Measurement saved locally")}
  catch(e){toast(e.message,true)}
});
$("exportCsv").addEventListener("click",()=>{if(state.activeSession)window.location.href="/api/surveys/"+state.activeSession+"/export.csv"});
function fillProjectForm(){const p=state.project;if(!p)return;$("projectName").value=p.name;$("planWidth").value=p.width_m;$("planHeight").value=p.height_m;$("wallHeight").value=p.wall_height_m;$("frequency").value=p.frequency_mhz;$("txPower").value=p.tx_power_dbm;$("routerX").value=p.router.x;$("routerY").value=p.router.y;renderWallList()}
function projectFromForm(){const p=state.project;return {...p,name:$("projectName").value||"My Home",width_m:Number($("planWidth").value),height_m:Number($("planHeight").value),wall_height_m:Number($("wallHeight").value),frequency_mhz:Number($("frequency").value),tx_power_dbm:Number($("txPower").value),router:{...p.router,x:Number($("routerX").value),y:Number($("routerY").value)}}}
async function saveProject(){
  try{const p=projectFromForm();const saved=await api("/api/project",{method:"PUT",body:JSON.stringify(p)});state.project=saved;fillProjectForm();$("savedLabel").textContent="SAVED · "+new Date().toLocaleTimeString();drawAllPlans();refreshStats();toast("Floor plan saved to local SQLite")}
  catch(e){toast(e.message,true)}
}
$("saveProject").addEventListener("click",saveProject);
function renderWallList(){$("wallList").innerHTML=(state.project?.walls||[]).map((w,i)=>'<div class="wall-row"><span>'+(i+1)+'. '+esc(w.material)+' · '+Math.hypot(w.x2-w.x1,w.y2-w.y1).toFixed(1)+' m</span><button data-remove-wall="'+i+'" title="Remove wall">×</button></div>').join("")||'<div class="empty">No internal walls added.</div>';$("wallCount").textContent=(state.project?.walls.length||0)+" walls"}
$("wallList").addEventListener("click",async e=>{const b=e.target.closest("[data-remove-wall]");if(!b)return;state.project.walls.splice(Number(b.dataset.removeWall),1);renderWallList();drawAllPlans();await saveProject()});
$("planMode").addEventListener("change",e=>{state.mode=e.target.value;state.wallStart=null;$("toolHelp").textContent=state.mode==="wall"?"Click two points on the plan to add a wall.":state.mode==="router"?"Click the plan to move the router.":"Choose Draw wall or Place router to edit the plan.";});
$("orbit").addEventListener("input",drawScene);
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
  const r=worldToCanvas(p.router.x,p.router.y,canvas);ctx.fillStyle="#66e2df";ctx.beginPath();ctx.arc(r.x,r.y,7,0,Math.PI*2);ctx.fill();ctx.strokeStyle="#66e2df55";ctx.lineWidth=8;ctx.beginPath();ctx.arc(r.x,r.y,13,0,Math.PI*2);ctx.stroke();ctx.fillStyle="#b9f6ef";ctx.font="10px Manrope";ctx.fillText("ROUTER",r.x+12,r.y-10);
  if(showPoints)state.points.forEach(point=>{const q=worldToCanvas(point.x,point.y,canvas);ctx.fillStyle=dbmColor(point.rssi_dbm);ctx.strokeStyle="#07111d";ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(q.x,q.y,5,0,Math.PI*2);ctx.fill();ctx.stroke()});
  if(state.selectedPoint&&canvas.id==="surveyCanvas"){const q=worldToCanvas(state.selectedPoint.x,state.selectedPoint.y,canvas);ctx.strokeStyle="#fff";ctx.setLineDash([4,3]);ctx.beginPath();ctx.arc(q.x,q.y,9,0,Math.PI*2);ctx.stroke();ctx.setLineDash([])}
}
function wallColor(m){return ({drywall:"#8cabc1",wood:"#c79c65",glass:"#74cad6",brick:"#cf806d",concrete:"#a5aebb",metal:"#a18ddd"})[m]||"#8cabc1"}
function drawAllPlans(){drawPlan($("planCanvas"));drawPlan($("surveyCanvas"),true);drawScene();renderWallList();if(state.project){$("planDimensions").textContent=state.project.width_m+" × "+state.project.height_m+" m"}}
function handlePlanClick(canvas,e,mode){
  if(!state.project)return;const rect=canvas.getBoundingClientRect();const pos=canvasToWorld(e.clientX-rect.left,e.clientY-rect.top,canvas);const p=state.project;
  if(pos.x<0||pos.y<0||pos.x>p.width_m||pos.y>p.height_m)return;
  if(mode==="survey"){state.selectedPoint=pos;$("selectedCoord").textContent=pos.x+" m, "+pos.y+" m";$("capturePoint").disabled=!state.activeSession||$("manualRssi").value==="";drawPlan(canvas,true);return}
  if(mode==="router"){p.router.x=pos.x;p.router.y=pos.y;$("routerX").value=pos.x;$("routerY").value=pos.y;drawAllPlans();$("savedLabel").textContent="UNSAVED CHANGES";return}
  if(mode==="wall"){
    if(!state.wallStart){state.wallStart=pos;$("toolHelp").textContent="First point set. Click the second point.";return}
    if(Math.hypot(pos.x-state.wallStart.x,pos.y-state.wallStart.y)<0.05){toast("Wall is too short",true);return}
    p.walls.push({x1:state.wallStart.x,y1:state.wallStart.y,x2:pos.x,y2:pos.y,material:$("wallMaterial").value});state.wallStart=null;$("toolHelp").textContent="Wall added. Click two more points to continue.";drawAllPlans();$("savedLabel").textContent="UNSAVED CHANGES";return;
  }
}
$("surveyCanvas").addEventListener("click",e=>handlePlanClick($("surveyCanvas"),e,"survey"));
$("planCanvas").addEventListener("click",e=>handlePlanClick($("planCanvas"),e,state.mode));
function drawScene(){
  const canvas=$("sceneCanvas");if(!canvas||!state.project)return;const {ctx,w,h}=canvasMetrics(canvas);const p=state.project;ctx.clearRect(0,0,w,h);ctx.fillStyle="#0a1321";ctx.fillRect(0,0,w,h);
  const scale=Math.min(w/(p.width_m+p.height_m+4),h/((p.width_m+p.height_m)*.58+p.wall_height_m*1.1))*0.82;
  const angle=Number($("orbit").value||0)*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle);
  const cx=w/2,cy=h*.72,zc=scale*.78;
  const project=(x,y,z=0)=>{const dx=x-p.width_m/2,dy=y-p.height_m/2,u=c*dx-s*dy,v=s*dx+c*dy;return {x:cx+(u-v)*scale,y:cy+(u+v)*scale*.48-z*zc}};
  const A=project(0,0),B=project(p.width_m,0),C=project(p.width_m,p.height_m),D=project(0,p.height_m);
  ctx.fillStyle="#142a3a";ctx.strokeStyle="#4b7187";ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.lineTo(C.x,C.y);ctx.lineTo(D.x,D.y);ctx.closePath();ctx.fill();ctx.stroke();
  for(let i=0;i<=10;i++){ctx.strokeStyle="#2b4154";ctx.lineWidth=.6;const x=p.width_m*i/10;const a=project(x,0),b=project(x,p.height_m);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();const y=p.height_m*i/10;const d=project(0,y),e=project(p.width_m,y);ctx.beginPath();ctx.moveTo(d.x,d.y);ctx.lineTo(e.x,e.y);ctx.stroke()}
  (p.walls||[]).forEach(wall=>{const a=project(wall.x1,wall.y1),b=project(wall.x2,wall.y2),at=project(wall.x1,wall.y1,p.wall_height_m),bt=project(wall.x2,wall.y2,p.wall_height_m);ctx.fillStyle=wallColor(wall.material)+"55";ctx.strokeStyle=wallColor(wall.material);ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.lineTo(bt.x,bt.y);ctx.lineTo(at.x,at.y);ctx.closePath();ctx.fill();ctx.stroke()});
  const r=project(p.router.x,p.router.y,0.15);ctx.fillStyle="#66e2df";ctx.beginPath();ctx.arc(r.x,r.y,6,0,Math.PI*2);ctx.fill();ctx.fillStyle="#bdf9f2";ctx.font="10px Manrope";ctx.fillText("ACCESS POINT",r.x+10,r.y-10);
  ctx.fillStyle="#7d95af";ctx.font="10px 'DM Mono'";ctx.fillText("ISOMETRIC FLOOR MODEL · "+p.width_m+" × "+p.height_m+" M",15,20);
}
async function loadCoverage(kind){
  const session=Number($("coverageSession").value||state.activeSession||0);
  if(kind==="measured"&&!session){toast("Choose a survey session first",true);return}
  try{
    const data=kind==="measured"?await api("/api/coverage/measured?session_id="+session+"&resolution=40"):await api("/api/coverage/predicted?resolution=40");
    state.coverage=data;state.coverageKind=kind;
    $("coverageTitle").textContent=kind==="measured"?"Measured signal heatmap":"Theoretical RF propagation model";
    $("coverageSubtitle").textContent=kind==="measured"?"IDW interpolation of "+data.point_count+" saved physical readings.":"Estimated from router position, frequency, distance and wall crossings.";
    $("coverageType").textContent=kind==="measured"?"MEASURED · IDW":"MODEL · ESTIMATE";
    $("coverageRange").textContent=data.min_dbm==null?"No data":data.min_dbm+" to "+data.max_dbm+" dBm";
    $("coverageCount").textContent=kind==="measured"?data.point_count+" survey points":"Frequency "+(data.frequency_mhz/1000).toFixed(1)+" GHz";
    drawHeat();toast(kind==="measured"?"Measured coverage calculated":"RF model calculated");
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
  if(state.coverageKind==="measured")state.points.forEach(pt=>{const x=left+pt.x/p.width_m*dw,y=top+dh-pt.y/p.height_m*dh;ctx.fillStyle="#fff";ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill()});
}
async function loadSessionDropdowns(){
  state.sessions=await api("/api/surveys");fillSessions();refreshStats();
}
$("coverageSession").addEventListener("change",()=>{});
boot().then(()=>loadSessionDropdowns().catch(()=>{}));
