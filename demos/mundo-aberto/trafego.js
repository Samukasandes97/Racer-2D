/* Trânsito do mundo aberto: carros 3D simples que seguem as ruas do mapa (vias.json), respeitam semáforo,
   limite de velocidade por tipo de via, distância do carro da frente e o jogador. Direita = mão de direção (Chicago). */
(function(){
'use strict';
const MPU=12;                                       // 1 unidade do mapa = 12 m
const T={ready:false,cars:[],lanes:[],nodes:[],sig:[],lim:0};
window.Trafego=T;
const hyp=Math.hypot;
let lanes=[],nodes=[],byNode=[],grid=new Map();
const GS=3;                                          // celula do indice espacial (unidades)
const PAL=[[.80,.10,.10],[.15,.30,.75],[.92,.92,.88],[.08,.08,.10],[.55,.58,.62],[.90,.72,.10],[.12,.50,.30],[.85,.45,.10],[.45,.20,.55]];
// ---------- carregar vias ----------
fetch('mapa/vias.json').then(r=>r.json()).then(v=>{
  nodes=v.nodes.map((n,i)=>({x:n[0],z:n[1],deg:n[2],in:[],out:[],off:Math.random()*36,i}));
  for(const e of v.edges){
    const P=e.p;let L=0;const cum=[0];for(let i=1;i<P.length;i++){L+=hyp(P[i][0]-P[i-1][0],P[i][1]-P[i-1][1]);cum.push(L)}
    if(L<.35)continue;
    const w=e.w,cls=w>=1.9?3:w>=1.25?2:w>=.8?1:0;           // 0 rua estreita, 1 rua, 2 avenida, 3 via rapida
    const limk=[30,40,55,80][cls],off=Math.max(.07,Math.min(.2,(w-.4)/4));
    for(const dir of [1,-1]){
      const pts=dir===1?P.map(p=>[p[0],p[1]]):P.slice().reverse().map(p=>[p[0],p[1]]);
      // eixo deslocado para a direita do sentido de marcha
      const q=[];for(let i=0;i<pts.length;i++){
        const a=pts[Math.max(0,i-1)],b=pts[Math.min(pts.length-1,i+1)];let dx=b[0]-a[0],dz=b[1]-a[1];const l=hyp(dx,dz)||1;dx/=l;dz/=l;
        q.push([pts[i][0]-dz*off,pts[i][1]+dx*off])}                 // direita = (-dz, dx)
      const cm=[0];for(let i=1;i<q.length;i++)cm.push(cm[i-1]+hyp(q[i][0]-q[i-1][0],q[i][1]-q[i-1][1]));
      const ln={id:lanes.length,a:dir===1?e.a:e.b,b:dir===1?e.b:e.a,pts:q,cum:cm,len:cm[cm.length-1],lim:limk/3.6,cls,rev:null,edge:e};
      lanes.push(ln)}
    lanes[lanes.length-1].rev=lanes[lanes.length-2];lanes[lanes.length-2].rev=lanes[lanes.length-1];
  }
  for(const l of lanes){nodes[l.a].out.push(l);nodes[l.b].in.push(l)}
  for(const l of lanes){            // direcao de chegada (grupo do semaforo)
    const p=l.pts,a=p[p.length-2],b=p[p.length-1];const dx=b[0]-a[0],dz=b[1]-a[1];l.grp=Math.abs(dz)>Math.abs(dx)?0:1;l.dir=[dx/(hyp(dx,dz)||1),dz/(hyp(dx,dz)||1)]}
  for(const n of nodes){const k=Math.floor(n.x/GS)+','+Math.floor(n.z/GS);(grid.get(k)||grid.set(k,[]).get(k)).push(n)}
  T.lanes=lanes;T.nodes=nodes;T.ready=true;
}).catch(e=>{T.error=String(e)});
// ---------- semaforo: ciclo de 36 s, verde 14 / amarelo 3 / tudo vermelho 1 ----------
T.light=function(n,grp,t){const c=(t+n.off)%36,ph=c<18?0:1,r=c%18;       // ph = grupo com verde
  if(ph!==grp)return 'R';if(r<14)return 'G';if(r<17)return 'Y';return 'R'};
T.hasLight=n=>n.deg>=3;
// ---------- util ----------
function lanePoint(l,s){s=Math.max(0,Math.min(l.len,s));const c=l.cum;let i=1;while(i<c.length-1&&c[i]<s)i++;const t=(s-c[i-1])/((c[i]-c[i-1])||1);
  return [l.pts[i-1][0]+(l.pts[i][0]-l.pts[i-1][0])*t,l.pts[i-1][1]+(l.pts[i][1]-l.pts[i-1][1])*t]}
function project(l,x,z,hint){let best=1e9,bs=0;const p=l.pts,c=l.cum;
  for(let i=1;i<p.length;i++){const ax=p[i-1][0],az=p[i-1][1],bx=p[i][0],bz=p[i][1],dx=bx-ax,dz=bz-az,L2=dx*dx+dz*dz||1;let t=((x-ax)*dx+(z-az)*dz)/L2;t=Math.max(0,Math.min(1,t));
    const d=hyp(x-(ax+dx*t),z-(az+dz*t));if(d<best){best=d;bs=c[i-1]+t*Math.sqrt(L2)}}
  return [bs,best]}
const angd=(a,b)=>{let d=a-b;while(d>Math.PI)d-=2*Math.PI;while(d<-Math.PI)d+=2*Math.PI;return d};
// ---------- carros ----------
const TYPES=[{L:.36,H:.05,cab:.17,cabH:.04,cabOff:-.03,w:.15,p:3},{L:.30,H:.05,cab:.19,cabH:.045,cabOff:-.04,w:.145,p:2},{L:.42,H:.075,cab:.34,cabH:.05,cabOff:-.02,w:.16,p:1}];
function pickType(){let r=Math.random()*6;for(const t of TYPES){if((r-=t.p)<0)return t}return TYPES[0]}
function spawn(px,pz,phd,t){
  if(!lanes.length)return false;
  // sorteia faixa perto do jogador (anel 4..11 un), preferindo fora do campo de visao
  for(let tr=0;tr<20;tr++){
    const l=lanes[(Math.random()*lanes.length)|0];if(l.len<.9)continue;
    const s=Math.random()*(l.len-.4)+.2,p=lanePoint(l,s),d=hyp(p[0]-px,p[1]-pz);
    if(d<4.5||d>11)continue;
    const ang=Math.atan2(p[0]-px,p[1]-pz);if(Math.abs(angd(ang,phd))<.7&&d<8)continue;      // nao nasce na cara do jogador
    if(T.cars.some(c=>hyp(c.x-p[0],c.z-p[1])<.7))continue;
    const q=lanePoint(l,s+.05);const hd=Math.atan2(q[0]-p[0],q[1]-p[1]);
    const ty=pickType();
    T.cars.push({x:p[0],z:p[1],hd,v:l.lim*.7,lane:l,s,ty,col:PAL[(Math.random()*PAL.length)|0],v0f:.88+Math.random()*.17,brake:0,next:null,stuck:0,id:Math.random()});
    return true}
  return false}
function chooseNext(c){const n=nodes[c.lane.b];let opts=n.out.filter(o=>o!==c.lane.rev);if(!opts.length)opts=n.out.slice();if(!opts.length)return null;
  // preferencia por seguir em frente
  let tot=0;const w=opts.map(o=>{const a=o.pts[1]||o.pts[0],b=o.pts[0];const dx=a[0]-b[0],dz=a[1]-b[1],l=hyp(dx,dz)||1;const cs=(dx*c.lane.dir[0]+dz*c.lane.dir[1])/l;const k=cs>.7?3:cs>-.2?1.2:.8;tot+=k;return k});
  let r=Math.random()*tot;for(let i=0;i<opts.length;i++){if((r-=w[i])<0)return opts[i]}return opts[0]}
T.update=function(dt,t,pl){            // pl: {x,z,hd,v(m/s)}
  if(!T.ready)return;dt=Math.min(dt,.05);
  const cars=T.cars;
  if(cars.length<T.max&&Math.random()<dt*4)spawn(pl.x,pl.z,pl.hd,t);
  for(let i=cars.length-1;i>=0;i--){const c=cars[i];if(hyp(c.x-pl.x,c.z-pl.z)>14.5||c.stuck>45)cars.splice(i,1)}
  for(const c of cars){
    const l=c.lane,f=[Math.sin(c.hd),Math.cos(c.hd)],r=[-f[1],f[0]];
    // --- quem esta a frente (carros e jogador) ---
    let gap=1e9,vl=0;
    const consider=(ox,oz,ov,ohd)=>{const dx=ox-c.x,dz=oz-c.z,a=dx*f[0]+dz*f[1];if(a<=0||a>3)return;const lat=Math.abs(dx*r[0]+dz*r[1]);
      if(lat>.12)return;const cs=Math.sin(ohd)*f[0]+Math.cos(ohd)*f[1];if(cs<.3)return;const g=a-.38;if(g<gap){gap=g;vl=ov*cs}};
    for(const o of cars)if(o!==c)consider(o.x,o.z,o.v,o.hd);
    consider(pl.x,pl.z,pl.v,pl.hd);
    // --- semaforo no fim da faixa ---
    const nb=nodes[l.b],dend=(l.len-c.s)-.34;                     // distancia ate a linha de retenção
    let light='G';if(T.hasLight(nb))light=T.light(nb,l.grp,t);
    if(light!=='G'&&dend>-.05){
      const dm=Math.max(dend,0)*MPU;
      if(light==='R'||(c.v*c.v/(2*4.2)<dm-1)){if(dend<gap){gap=Math.max(dend,0)+.02;vl=0}}}
    // --- limite e curva ---
    let v0=l.lim*c.v0f;
    const nl=c.next||(c.next=chooseNext(c));
    if(nl&&l.len-c.s<.55){const a=l.dir,b=[nl.pts[1][0]-nl.pts[0][0],nl.pts[1][1]-nl.pts[0][1]];const bl=hyp(b[0],b[1])||1;const cs=(a[0]*b[0]+a[1]*b[1])/bl;if(cs<.75)v0=Math.min(v0,cs<.2?4.2:6.5)}
    // --- IDM ---
    const A=2.6,B=3.6,Th=1.2,s0=2.2;
    const dv=c.v-vl,sg=gap*MPU;
    const sstar=s0+Math.max(0,c.v*Th+c.v*dv/(2*Math.sqrt(A*B)));
    let acc=A*(1-Math.pow(c.v/Math.max(v0,.5),4)-(gap<1e8?Math.pow(sstar/Math.max(sg,.3),2):0));
    acc=Math.max(-9,acc);
    c.v=Math.max(0,c.v+acc*dt);c.brake=acc<-1.2?1:c.brake*(1-Math.min(1,dt*6));
    c.stuck=c.v<.3?c.stuck+dt:0;
    // --- avanca: persegue um ponto a frente na faixa ---
    const pr=project(l,c.x,c.z);c.s=Math.max(c.s,pr[0]);
    const look=Math.max(.16,c.v/MPU*.45+.1);
    let tp,ds=c.s+look;
    if(ds>l.len&&nl){const rest=ds-l.len;tp=lanePoint(nl,Math.min(nl.len,rest+.02))}else tp=lanePoint(l,ds);
    const want=Math.atan2(tp[0]-c.x,tp[1]-c.z);let dh=angd(want,c.hd);const maxr=Math.max(.6,c.v/2.7*Math.tan(.55));
    c.hd+=Math.max(-maxr*dt,Math.min(maxr*dt,dh));
    c.x+=Math.sin(c.hd)*c.v/MPU*dt;c.z+=Math.cos(c.hd)*c.v/MPU*dt;
    if(c.s>=l.len-.02&&nl){c.lane=nl;c.s=project(nl,c.x,c.z)[0];c.next=null}
    else if(c.s>=l.len-.02&&!nl){c.stuck+=dt}
  }
};
// ---------- colisao com o jogador (3 circulos de cada lado) ----------
T.collide=function(pl){const out={hit:false};
  for(const c of T.cars){const dx=c.x-pl.x,dz=c.z-pl.z;if(Math.abs(dx)>.5||Math.abs(dz)>.5)continue;
    const f=[Math.sin(c.hd),Math.cos(c.hd)],pf=[Math.sin(pl.hd),Math.cos(pl.hd)];
    let best=1e9;for(const a of [-.12,0,.12])for(const b of [-.12,0,.12]){const d=hyp(c.x+f[0]*a-(pl.x+pf[0]*b),c.z+f[1]*a-(pl.z+pf[1]*b));if(d<best)best=d}
    if(best<.125){out.hit=true;out.car=c;out.dx=pl.x-c.x;out.dz=pl.z-c.z;out.rv=hyp(pl.v-c.v*(f[0]*pf[0]+f[1]*pf[1]),0);return out}}
  return out};
// ---------- desenho ----------
T.draw=function(W3,pl,t,gy){
  const R=11.5;
  for(const c of T.cars){
    if(hyp(c.x-pl.x,c.z-pl.z)>R)continue;
    const h=W3.height(c.x,c.z,gy+.05,.12);const y=h===null?gy:h;const ty=c.ty,hl=ty.L/2,w=ty.w/2,hd=c.hd;
    const [r,g,b]=c.col,s=Math.sin(hd),co=Math.cos(hd);
    W3.box(c.x,y+.028+ty.H/2*.9,c.z,hl,ty.H/2,w,hd,r,g,b,0);                                   // carroceria
    const cx=c.x+s*ty.cabOff,cz=c.z+co*ty.cabOff;
    W3.box(cx,y+.028+ty.H*.9+ty.cabH/2,cz,ty.cab/2,ty.cabH/2,w*.88,hd,.08,.11,.17,0);          // vidros
    W3.box(cx,y+.028+ty.H*.9+ty.cabH+.004,cz,ty.cab/2*.92,.004,w*.78,hd,r*.9,g*.9,b*.9,0);       // teto
    for(const fx of [hl*.62,-hl*.62])for(const sd of [-1,1]){                                     // rodas
      W3.box(c.x+s*fx-co*sd*w,y+.02,c.z+co*fx+s*sd*w,.028,.02,.012,hd,.03,.03,.035,0)}
    for(const sd of [-1,1]){                                                                      // faroi / lanterna
      W3.box(c.x+s*hl*.99-co*sd*w*.7,y+.045,c.z+co*hl*.99+s*sd*w*.7,.006,.009,.02,hd,1,.95,.75,1);
      const br=c.brake>.5;W3.box(c.x-s*hl*.99-co*sd*w*.7,y+.045,c.z-co*hl*.99+s*sd*w*.7,.006,.009,.02,hd,br?1:.7,br?.1:.05,br?.1:.05,br?1:.75)}
  }
  // semaforos perto do jogador
  const gx=Math.floor(pl.x/GS),gz=Math.floor(pl.z/GS),rr=Math.ceil(R/GS);
  for(let i=-rr;i<=rr;i++)for(let j=-rr;j<=rr;j++){const arr=grid.get((gx+i)+','+(gz+j));if(!arr)continue;
    for(const n of arr){if(!T.hasLight(n)||hyp(n.x-pl.x,n.z-pl.z)>R)continue;
      const hh=W3.height(n.x,n.z,gy+.3,.3);const y=hh===null?gy:hh;
      for(const l of n.in){const d=l.dir,rt=[-d[1],d[0]],px=n.x-d[0]*.36+rt[0]*.27,pz=n.z-d[1]*.36+rt[1]*.27,st=T.light(n,l.grp,t);
        W3.box(px,y+.07,pz,.004,.07,.004,0,.15,.15,.16,0);                                         // poste
        const hd=Math.atan2(-d[0],-d[1]);                                                          // cabeca olha para quem chega
        W3.box(px,y+.155,pz,.012,.036,.014,hd,.04,.04,.045,0);
        const lamp=(k,col,on)=>W3.box(px-d[0]*.013*-1*-1,y+.155+k*.022,pz-d[1]*.013*-1*-1,.004,.009,.009,hd,col[0]*(on?1:.18),col[1]*(on?1:.18),col[2]*(on?1:.18),on?1:0);
        lamp(1,[1,.1,.1],st==='R');lamp(0,[1,.8,.05],st==='Y');lamp(-1,[.1,1,.25],st==='G')}}}
};
T.max=26;
})();
