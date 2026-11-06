/* Mundo 3D do mapa (WebGL puro, sem bibliotecas): desenha os blocos do mapa para um canvas pequeno (480x270),
   que o jogo cola por baixo do carro 2D e do cockpit. Também responde "qual a altura do chão aqui?" (colisão). */
(function(){
'use strict';
const MAP='mapa/';
const cvs=document.createElement('canvas');cvs.width=480;cvs.height=270;
const gl=cvs.getContext('webgl',{alpha:true,antialias:false,premultipliedAlpha:false,preserveDrawingBuffer:false});
const W3={canvas:cvs,ready:false,start:{x:0,z:0,hd:0},cfg:null,grid:null,loaded:0};
window.World3D=W3;
if(!gl){W3.error='sem WebGL';return}
// ---------- matrizes (coluna-maior) ----------
const m4={
  persp(f,a,n,r){const t=1/Math.tan(f/2),o=new Float32Array(16);o[0]=t/a;o[5]=t;o[10]=(r+n)/(n-r);o[11]=-1;o[14]=2*r*n/(n-r);return o},
  look(e,c,u){let zx=e[0]-c[0],zy=e[1]-c[1],zz=e[2]-c[2],l=Math.hypot(zx,zy,zz);zx/=l;zy/=l;zz/=l;
    let xx=u[1]*zz-u[2]*zy,xy=u[2]*zx-u[0]*zz,xz=u[0]*zy-u[1]*zx;l=Math.hypot(xx,xy,xz);xx/=l;xy/=l;xz/=l;
    const yx=zy*xz-zz*xy,yy=zz*xx-zx*xz,yz=zx*xy-zy*xx,o=new Float32Array(16);
    o[0]=xx;o[1]=yx;o[2]=zx;o[4]=xy;o[5]=yy;o[6]=zy;o[8]=xz;o[9]=yz;o[10]=zz;
    o[12]=-(xx*e[0]+xy*e[1]+xz*e[2]);o[13]=-(yx*e[0]+yy*e[1]+yz*e[2]);o[14]=-(zx*e[0]+zy*e[1]+zz*e[2]);o[15]=1;return o},
  mul(a,b){const o=new Float32Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k];o[i*4+j]=s}return o}
};
// ---------- shader ----------
const VS=`attribute vec3 aP;attribute vec2 aT;attribute float aS;uniform mat4 uM;uniform vec3 uMn,uExt;varying vec2 vT;varying float vS;varying vec3 vW;varying float vD;
void main(){vec3 p=uMn+aP*uExt;vec4 c=uM*vec4(p,1.);gl_Position=c;vT=aT;vS=aS;vW=p;vD=c.w;}`;
const FS=`precision highp float;uniform sampler2D uTex;uniform vec3 uCar,uFwd,uFog,uTint;uniform vec2 uFogR;uniform float uHead,uTime;
varying vec2 vT;varying float vS;varying vec3 vW;varying float vD;
void main(){vec3 t=texture2D(uTex,vT).rgb;if(t.r+t.g+t.b<.045)discard;
 vec3 col=t*vS*uTint;
 vec3 d=vW-uCar;float al=dot(d.xz,uFwd.xz);float ac=abs(d.x*uFwd.z-d.z*uFwd.x);
 float cone=uHead*step(0.,al)*smoothstep(2.4,.05,al)*smoothstep(.10+al*.34,0.,ac)*smoothstep(.55,.0,abs(d.y));
 col+=t*vec3(1.15,1.02,.8)*cone*1.1;
 float lum=dot(t,vec3(.3,.59,.11));col+=t*smoothstep(.55,.9,lum)*.10;      /* janelas/placas claras brilham um pouco */
 float f=clamp((vD-uFogR.x)/(uFogR.y-uFogR.x),0.,1.);col=mix(col,uFog,f*f*(3.-2.*f));
 gl_FragColor=vec4(col,1.);}`;
function sh(t,s){const o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);if(!gl.getShaderParameter(o,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(o));return o}
const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,VS));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);
if(!gl.getProgramParameter(pr,gl.LINK_STATUS)){W3.error=gl.getProgramInfoLog(pr);return}
gl.useProgram(pr);
const A={P:gl.getAttribLocation(pr,'aP'),T:gl.getAttribLocation(pr,'aT'),S:gl.getAttribLocation(pr,'aS')};
const U={};['uM','uMn','uExt','uTex','uCar','uFwd','uFog','uTint','uFogR','uHead','uTime'].forEach(n=>U[n]=gl.getUniformLocation(pr,n));
gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);
const idxExt=gl.getExtension('OES_element_index_uint');
// ---------- dados ----------
let tex=null;const tiles=new Map();let index=[];const loading=new Set();
const img=new Image();img.onload=()=>{tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);
  gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,img);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE)};
img.src=MAP+'atlas.png';
Promise.all([fetch(MAP+'tiles.json').then(r=>r.json()),fetch(MAP+'grid.wav').then(r=>r.arrayBuffer()),fetch(MAP+'start.json').then(r=>r.json())]).then(([cfg,g,st])=>{
  W3.cfg=cfg;W3.grid=new Int16Array(g);W3.start=st;index=cfg.tiles;W3.ready=true}).catch(e=>{W3.error=String(e)});
// altura do chao em camadas (pontes, rampas, tuneis). Retorna a camada mais alta que o carro alcanca (<= gy+degrau); null = parede/vazio
W3.height=function(x,z,gy){const c=W3.cfg;if(!c)return 0;const ix=Math.floor((x-c.x0)/c.CELL),iz=Math.floor((z-c.z0)/c.CELL);
  if(ix<0||iz<0||ix>=c.GW||iz>=c.GH)return null;const n=c.GW*c.GH,lim=(gy===undefined?9:gy)+.14;let best=null;
  for(let l=0;l<c.LAY;l++){const v=W3.grid[l*n+iz*c.GW+ix];if(v===-32768)break;const h=v/1000;if(h<=lim&&(best===null||h>best))best=h}
  return best};
let inflight=0;
function loadTile(t){if(loading.has(t.f)||tiles.has(t.f))return;loading.add(t.f);inflight++;
  fetch(MAP+t.f).then(r=>r.arrayBuffer()).then(b=>{
    const dv=new DataView(b),nv=dv.getUint32(0,true),ni=dv.getUint32(4,true);let o=8;
    const q=new Uint16Array(b,o,nv*3);o+=nv*6;const uv=new Uint16Array(b,o,nv*2);o+=nv*4;const sd=new Uint8Array(b,o,nv);o+=nv+((4-nv%4)%4);
    const ind=new Uint16Array(b,o,ni);
    const mk=(tp,d)=>{const bf=gl.createBuffer();gl.bindBuffer(tp,bf);gl.bufferData(tp,d,gl.STATIC_DRAW);return bf};
    const mn=t.mn,ex=t.ext,rad=.5*Math.hypot(ex[0],ex[1],ex[2]);
    tiles.set(t.f,{t,bp:mk(gl.ARRAY_BUFFER,q),bu:mk(gl.ARRAY_BUFFER,uv),bs:mk(gl.ARRAY_BUFFER,sd),bi:mk(gl.ELEMENT_ARRAY_BUFFER,ind),n:ni,c:[mn[0]+ex[0]/2,mn[1]+ex[1]/2,mn[2]+ex[2]/2],r:rad});
    loading.delete(t.f);inflight--;W3.loaded=tiles.size}).catch(()=>{loading.delete(t.f);inflight--})}
// o mapa inteiro fica na memoria (nada some): carrega do mais perto do carro para o mais longe, 6 por vez
function stream(x,z){const c=W3.cfg;if(!c||inflight>=6||tiles.size>=index.length)return;
  const todo=index.filter(t=>!tiles.has(t.f)&&!loading.has(t.f));
  todo.sort((a,b)=>Math.hypot(a.mn[0]+a.ext[0]/2-x,a.mn[2]+a.ext[2]/2-z)-Math.hypot(b.mn[0]+b.ext[0]/2-x,b.mn[2]+b.ext[2]/2-z));
  for(const t of todo){if(inflight>=6)break;loadTile(t)}}
W3.tilesReady=(x,z,R)=>{const c=W3.cfg;if(!c)return false;for(const t of index){if(Math.hypot(t.mn[0]+t.ext[0]/2-x,t.mn[2]+t.ext[2]/2-z)<R+t.ext[0]*.5&&!tiles.has(t.f))return false}return true};
W3.stream=stream;
W3.progress=()=>index.length?tiles.size/index.length:0;
// cam: {eye:[x,y,z], at:[x,y,z], fov(rad), far}; car:{p:[x,y,z], fwd:[x,z], head:0..1}; fog:[r,g,b]
W3.render=function(cam,car,fog,tint,time){
  stream(cam.eye[0],cam.eye[2]);
  gl.viewport(0,0,480,270);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  if(!tex)return;
  const M=m4.mul(m4.persp(cam.fov,480/270,.02,cam.far),m4.look(cam.eye,cam.at,[0,1,0]));
  gl.uniformMatrix4fv(U.uM,false,M);gl.uniform3f(U.uCar,car.p[0],car.p[1],car.p[2]);gl.uniform3f(U.uFwd,car.fwd[0],0,car.fwd[1]);
  gl.uniform3f(U.uFog,fog[0],fog[1],fog[2]);gl.uniform3f(U.uTint,tint[0],tint[1],tint[2]);gl.uniform2f(U.uFogR,cam.far*.35,cam.far);gl.uniform1f(U.uHead,car.head);gl.uniform1f(U.uTime,time||0);
  gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,tex);gl.uniform1i(U.uTex,0);
  gl.enableVertexAttribArray(A.P);gl.enableVertexAttribArray(A.T);gl.enableVertexAttribArray(A.S);
  const fx=cam.at[0]-cam.eye[0],fy=cam.at[1]-cam.eye[1],fz=cam.at[2]-cam.eye[2],fl=Math.hypot(fx,fy,fz);
  for(const o of tiles.values()){
    const dx=o.c[0]-cam.eye[0],dy=o.c[1]-cam.eye[1],dz=o.c[2]-cam.eye[2];
    if(Math.hypot(dx,dy,dz)>cam.far+o.r||(dx*fx+dy*fy+dz*fz)/fl<-o.r)continue;
    gl.uniform3f(U.uMn,o.t.mn[0],o.t.mn[1],o.t.mn[2]);gl.uniform3f(U.uExt,o.t.ext[0],o.t.ext[1],o.t.ext[2]);
    gl.bindBuffer(gl.ARRAY_BUFFER,o.bp);gl.vertexAttribPointer(A.P,3,gl.UNSIGNED_SHORT,true,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,o.bu);gl.vertexAttribPointer(A.T,2,gl.UNSIGNED_SHORT,true,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,o.bs);gl.vertexAttribPointer(A.S,1,gl.UNSIGNED_BYTE,true,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,o.bi);gl.drawElements(gl.TRIANGLES,o.n,gl.UNSIGNED_SHORT,0)}
};
// projeta um ponto do mundo para a tela 480x270 (para achar o horizonte)
W3.project=function(cam,p){const M=m4.mul(m4.persp(cam.fov,480/270,.02,cam.far),m4.look(cam.eye,cam.at,[0,1,0]));
  const x=M[0]*p[0]+M[4]*p[1]+M[8]*p[2]+M[12],y=M[1]*p[0]+M[5]*p[1]+M[9]*p[2]+M[13],w=M[3]*p[0]+M[7]*p[1]+M[11]*p[2]+M[15];
  return [(x/w*.5+.5)*480,(1-(y/w*.5+.5))*270,w]};
})();
