/* Trânsito do mundo aberto: carros 3D simples que seguem as ruas do mapa (vias.json), respeitam semáforo,
   limite de velocidade por tipo de via, distância do carro da frente e o jogador. Direita = mão de direção (Chicago). */
(function(){
'use strict';
const MPU=24;                                       // 1 unidade do mapa = 24 m (carro 4,3 m = .18)
const T={ready:false,cars:[],lanes:[],nodes:[],sig:[],lim:0};
window.Trafego=T;
const hyp=Math.hypot;
let lanes=[],nodes=[],byNode=[],grid=new Map();
const GS=3;                                          // celula do indice espacial (unidades)
const PAL=[[.80,.10,.10],[.15,.30,.75],[.92,.92,.88],[.08,.08,.10],[.55,.58,.62],[.90,.72,.10],[.12,.50,.30],[.85,.45,.10],[.45,.20,.55]];
// ---------- carregar vias ----------
let EDGES=[];
fetch('mapa/vias.json').then(r=>r.json()).then(v=>{
  nodes=v.nodes.map((n,i)=>({x:n[0],z:n[1],deg:n[2],in:[],out:[],off:Math.random()*36,i,wmax:0}));
  for(const e of v.edges){nodes[e.a].wmax=Math.max(nodes[e.a].wmax,e.w);nodes[e.b].wmax=Math.max(nodes[e.b].wmax,e.w)}
  EDGES=v.edges;T.edges=EDGES;T.nodes=nodes;T.loaded=true;
}).catch(e=>{T.error=String(e)});
// faixa deslocada p/ a direita do sentido de marcha (direita = (-dz, dx))
function buildLane(e,dir,off){
  const P=e.p,pts=dir===1?P.map(p=>[p[0],p[1]]):P.slice().reverse().map(p=>[p[0],p[1]]);
  const q=[];for(let i=0;i<pts.length;i++){
    const a=pts[Math.max(0,i-1)],b=pts[Math.min(pts.length-1,i+1)];let dx=b[0]-a[0],dz=b[1]-a[1];const l=hyp(dx,dz)||1;dx/=l;dz/=l;
    q.push([pts[i][0]-dz*off,pts[i][1]+dx*off])}
  const cm=[0];for(let i=1;i<q.length;i++)cm.push(cm[i-1]+hyp(q[i][0]-q[i-1][0],q[i][1]-q[i-1][1]));
  return {pts:q,cum:cm,len:cm[cm.length-1],a:dir===1?e.a:e.b,b:dir===1?e.b:e.a}}
// ponto da faixa e' livre se o carro inteiro (3 pontos laterais) esta sobre chao e sem obstaculo
function laneClear(W3,L){let bad=0,hp=null;const p=L.pts;
  for(let i=1;i<p.length;i++){const dx=p[i][0]-p[i-1][0],dz=p[i][1]-p[i-1][1],l=hyp(dx,dz)||1,k=Math.max(1,Math.ceil(l/.025)),fx=dx/l,fz=dz/l;
    for(let j=0;j<=k;j++){const t=j/k,x=p[i-1][0]+dx*t,z=p[i-1][1]+dz*t;
      const h=hp===null?W3.height(x,z,0,.06):W3.height(x,z,hp,.02);                 // altura encadeada: o carro (degrau max .025) consegue seguir
      if(h===null||W3.obs(x,z)){bad++;continue}
      hp=h;
      for(const o of [-.055,-.03,.03,.055])for(const q of [-.09,0,.09]){const px=x-fz*o+fx*q,pz=z+fx*o+fz*q;if(W3.height(px,pz,h,.02)===null||W3.obs(px,pz))bad++}}}
  return bad}
function validate(W3){
  lanes=[];let nbad=0,tot=0;
  for(const e of EDGES){
    const w=e.w,cls=w>=1.9?3:w>=1.25?2:w>=.8?1:0,limk=[30,40,55,80][cls];
    const base=Math.max(.07,Math.min(.22,(w/2-.16)/2+.02));
    const pair=[];
    for(const dir of [1,-1]){tot++;let L=null;
      for(const k of [1,.85,.7,.55,.4]){const c=buildLane(e,dir,base*k);if(c.len<.3)break;if(laneClear(W3,c)===0){L=c;L.off=base*k;break}}
      if(!L){nbad++;pair.push(null);continue}
      Object.assign(L,{id:lanes.length,lim:limk/3.6,cls,rev:null,edge:e});pair.push(L);lanes.push(L)}
    if(pair[0]&&pair[1]){pair[0].rev=pair[1];pair[1].rev=pair[0]}
  }
  for(const n of nodes){n.in=[];n.out=[]}
  for(const l of lanes){nodes[l.a].out.push(l);nodes[l.b].in.push(l)}
  for(const l of lanes){const p=l.pts,a=p[p.length-2],b=p[p.length-1];const dx=b[0]-a[0],dz=b[1]-a[1],L=hyp(dx,dz)||1;
    l.grp=Math.abs(dz)>Math.abs(dx)?0:1;l.dir=[dx/L,dz/L];
    // linha de retencao: antes da faixa de pedestres do cruzamento (largura da rua que cruza)
    const nb=nodes[l.b];l.stop=Math.max(.2,Math.min(.6,nb.wmax/2*.85));if(l.stop>l.len*.7)l.stop=l.len*.4}
  // conexoes dentro do cruzamento: curva suave de uma faixa para a proxima (so se estiver livre); esquerda so sem fluxo contrario
  let nc=0,ncBad=0;const conns=[];
  for(const n of nodes){for(const l of n.in){l.conns=[];
    for(const o of n.out){if(o===l.rev)continue;
      const od=[o.pts[1][0]-o.pts[0][0],o.pts[1][1]-o.pts[0][1]],ol=hyp(od[0],od[1])||1;od[0]/=ol;od[1]/=ol;
      const dif=angd(Math.atan2(od[0],od[1]),Math.atan2(l.dir[0],l.dir[1]));
      if(dif>.5&&n.in.some(i=>i!==l&&i.dir[0]*l.dir[0]+i.dir[1]*l.dir[1]<-.7))continue;
      const P0=l.pts[l.pts.length-1],P3=o.pts[0],dd=hyp(P3[0]-P0[0],P3[1]-P0[1]),k=Math.max(.04,dd*.45);
      const P1=[P0[0]+l.dir[0]*k,P0[1]+l.dir[1]*k],P2=[P3[0]-od[0]*k,P3[1]-od[1]*k],pts=[];
      for(let i=0;i<=8;i++){const u=i/8,v=1-u;pts.push([v*v*v*P0[0]+3*v*v*u*P1[0]+3*v*u*u*P2[0]+u*u*u*P3[0],v*v*v*P0[1]+3*v*v*u*P1[1]+3*v*u*u*P2[1]+u*u*u*P3[1]])}
      const cm=[0];for(let i=1;i<pts.length;i++)cm.push(cm[i-1]+hyp(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));
      const cn={pts,cum:cm,len:cm[cm.length-1],isConn:true,to:o,from:l,turn:dif,lim:Math.abs(dif)<.5?(dd>.07?Math.min(l.lim,5.5):l.lim):(dif>0?6:5),cls:l.cls,dir:od,a:n.i,b:n.i,grp:l.grp,id:-1-conns.length,off:l.off};
      nc++;if(cn.len>.01&&laneClear(W3,cn)>0){ncBad++;continue}
      l.conns.push(cn);conns.push(cn)}}}
  T.conns=conns;
  {const par=nodes.map((_,i)=>i),fd=x=>{while(par[x]!==x){par[x]=par[par[x]];x=par[x]}return x};   // cruzamentos vizinhos (<1,1 un.) compartilham o mesmo ciclo de semaforo
   for(let i=0;i<nodes.length;i++)if(nodes[i].deg>=3)for(let j=i+1;j<nodes.length;j++)if(nodes[j].deg>=3&&hyp(nodes[i].x-nodes[j].x,nodes[i].z-nodes[j].z)<1.1)par[fd(i)]=fd(j);
   for(const n of nodes)n.off=nodes[fd(n.i)].off}
  grid=new Map();for(const n of nodes){const k=Math.floor(n.x/GS)+','+Math.floor(n.z/GS);(grid.get(k)||grid.set(k,[]).get(k)).push(n)}
  T.lanes=lanes;T.stats={lanes:lanes.length,rejeitadas:nbad,total:tot,conexoes:conns.length,conexoesRejeitadas:ncBad};T.ready=true}
// ---------- semaforo: ciclo de 36 s, verde 14 / amarelo 3 / tudo vermelho 1 ----------
T.light=function(n,grp,t){const c=(t+n.off)%36,ph=c<18?0:1,r=c%18;       // ph = grupo com verde
  if(ph!==grp)return 'R';if(r<11)return 'G';if(r<14)return 'Y';return 'R'};
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
const TYPES=[{L:.16,H:.026,cab:.08,cabH:.02,cabOff:-.013,w:.066,p:3},{L:.135,H:.026,cab:.085,cabH:.02,cabOff:-.018,w:.064,p:2},{L:.19,H:.04,cab:.15,cabH:.024,cabOff:-.01,w:.072,p:1}];
function pickType(){let r=Math.random()*6;for(const t of TYPES){if((r-=t.p)<0)return t}return TYPES[0]}
function spawn(px,pz,phd,t){
  if(!lanes.length)return false;
  // sorteia faixa perto do jogador (anel 4..11 un), preferindo fora do campo de visao
  for(let tr=0;tr<20;tr++){
    if(!lanes.cum){let a=0;lanes.cum=lanes.map(x=>a+=x.len)}let rr=Math.random()*lanes.cum[lanes.cum.length-1],lo=0,hi=lanes.cum.length-1;while(lo<hi){const m=(lo+hi)>>1;if(lanes.cum[m]<rr)lo=m+1;else hi=m}
    const l=lanes[lo];if(l.len<.45)continue;
    const s=Math.random()*(l.len-.2)+.1,p=lanePoint(l,s),d=hyp(p[0]-px,p[1]-pz);
    if(d<3.5||d>10)continue;
    const ang=Math.atan2(p[0]-px,p[1]-pz);if(Math.abs(angd(ang,phd))<.7&&d<7)continue;      // nao nasce na cara do jogador
    if(T.cars.some(c=>hyp(c.x-p[0],c.z-p[1])<.9))continue;
    if(T.cars.reduce((n,c)=>n+(hyp(c.x-p[0],c.z-p[1])<2.5?1:0),0)>=2)continue;               // espalha: no maximo 2 carros por ~60 m ao redor
    const q=lanePoint(l,s+.03);const hd=Math.atan2(q[0]-p[0],q[1]-p[1]);
    const ty=pickType();
    T.cars.push({x:p[0],z:p[1],hd,v:l.lim*.45,lane:l,s,ty,col:PAL[(Math.random()*PAL.length)|0],v0f:.88+Math.random()*.17,brake:0,next:null,stuck:0,id:Math.random()});
    return true}
  return false}
function newGoal(c){const a=c.hd+(Math.random()-.5)*1.6,d=5+Math.random()*6;c.goal=[c.x+Math.sin(a)*d,c.z+Math.cos(a)*d];c.goalT=40+Math.random()*50}
function chooseNext(c){const l=c.lane;if(l.isConn)return l.to;const opts=l.conns||[];if(!opts.length)return null;
  if(!c.goal||hyp(c.x-c.goal[0],c.z-c.goal[1])<1.5||c.goalT<=0||((c.goal[0]-c.x)*Math.sin(c.hd)+(c.goal[1]-c.z)*Math.cos(c.hd))<0)newGoal(c);
  if(opts.length>1){let best=null,bs=1e9;for(const o of opts){const e=o.to&&o.to.pts?o.to.pts[o.to.pts.length-1]:(o.pts?o.pts[o.pts.length-1]:null);if(!e){continue}
      const sc=hyp(e[0]-c.goal[0],e[1]-c.goal[1])+Math.random()*1.2;if(sc<bs){bs=sc;best=o}}
    if(best)return best}
  let tot=0;const w=opts.map(o=>{const k=Math.abs(o.turn)<.5?3:.9;tot+=k;return k});
  let r=Math.random()*tot;for(let i=0;i<opts.length;i++){if((r-=w[i])<0)return opts[i]}return opts[0]}
T.update=function(dt,t,pl){            // pl: {x,z,hd,v(m/s)}
  if(!T.ready)return;dt=Math.min(dt,.05);
  const cars=T.cars;
  if(cars.length<T.max&&Math.random()<dt*4)spawn(pl.x,pl.z,pl.hd,t);
  const W3=World3D;
  for(let i=cars.length-1;i>=0;i--){const c=cars[i];
    // rede de seguranca: carro dentro de parede/obstaculo por >1 s, ou sobreposto a outro por >1,5 s, e' removido (nao fica bug visivel)
    const hc=W3.height(c.x,c.z,0,.06);c.bad=(hc===null||W3.obs(c.x,c.z))?(c.bad||0)+dt:0;
    let ov=false;if(c.uid)for(const o of cars){if(o!==c&&o.uid&&o.uid<c.uid&&hyp(o.x-c.x,o.z-c.z)<.1){ov=true;break}}c.ovT=ov?(c.ovT||0)+dt:0;
    if(hyp(c.x-pl.x,c.z-pl.z)>11.5||c.stuck>25||c.bad>.6||c.ovT>.5)cars.splice(i,1)}
  for(const c of cars){if(c.goalT>0)c.goalT-=dt;
    const l=c.lane,f=[Math.sin(c.hd),Math.cos(c.hd)],r=[-f[1],f[0]];
    // --- quem esta a frente (carros e jogador) ---
    let gap=1e9,vl=0;
    const consider=(ox,oz,ov,ohd)=>{const dx=ox-c.x,dz=oz-c.z,a=dx*f[0]+dz*f[1];if(a<=0||a>1.4)return;const lat=Math.abs(dx*r[0]+dz*r[1]);
      if(lat>.06)return;const cs=Math.sin(ohd)*f[0]+Math.cos(ohd)*f[1];if(cs<.3)return;const g=a-.18;if(g<gap){gap=g;vl=ov*cs}};
    for(const o of cars)if(o!==c)consider(o.x,o.z,o.v,o.hd);
    // conflito previsto (cruzamentos): se o caminho de outro carro cruza o meu em ate 1,4 s, o mais novo cede
    if(!c.uid)c.uid=(T._n=(T._n||0)+1);
    if(c.stuck<5)for(const o of cars){if(o===c||!o.uid||o.uid>c.uid)continue;const rx=o.x-c.x,rz=o.z-c.z,d0=Math.hypot(rx,rz);if(d0>.7||d0<.001)continue;
      if(rx*f[0]+rz*f[1]<-.04)continue;                                       // quem esta atras de mim nao me interessa
      const vx=(Math.sin(o.hd)*o.v-f[0]*c.v)/MPU,vz=(Math.cos(o.hd)*o.v-f[1]*c.v)/MPU,vv=vx*vx+vz*vz;
      const tau=vv>1e-6?Math.max(0,Math.min(1.4,-(rx*vx+rz*vz)/vv)):0;const dm=Math.hypot(rx+vx*tau,rz+vz*tau);
      if(dm<.13){const g=d0-.17;if(g<gap){gap=Math.max(g,0);vl=Math.min(vl,o.v*.5)}}}
    // lider pela propria faixa (e pela proxima/conexao): mesmo com pequeno desvio lateral, quem esta na frente na rota conta
    {const nl0=c.next||(c.next=chooseNext(c));const L0=l.len-c.s;
     for(const o of cars){if(o===c)continue;let dd=-1;
       if(o.lane===l&&o.s>c.s)dd=o.s-c.s;
       else if(nl0&&o.lane===nl0)dd=L0+o.s;
       else if(nl0&&nl0.isConn&&o.lane===nl0.to)dd=L0+nl0.len+o.s;
       if(dd<0||dd>1.4)continue;const g=dd-.18;if(g<gap){gap=g;vl=o.v}}}
    consider(pl.x,pl.z,pl.v,pl.hd);
    // --- semaforo no fim da faixa ---
    const nb=nodes[l.b],dend=l.isConn?1e9:(l.len-l.stop)-(c.s+.09);          // distancia ate a linha de retencao
    let light='G';if(!l.isConn&&T.hasLight(nb))light=T.light(nb,l.grp,t);
    if(light!=='G'&&dend>-.05){
      const dm=Math.max(dend,0)*MPU;
      if(light==='R'||(c.v*c.v/(2*4.2)<dm-1)){if(dend<gap){gap=Math.max(dend,0)+.02;vl=0}}}
    // --- limite e curva ---
    let v0=l.lim*c.v0f;
    const nl=c.next||(c.next=chooseNext(c));
    if(!nl){const de=(l.len-c.s)-.1;if(de<gap){gap=Math.max(de,0)+.02;vl=0}}      // fim de rua sem saida: para (e some depois)
    if(l.isConn)v0=Math.min(v0,l.lim);else if(nl&&nl.isConn&&l.len-c.s<.35)v0=Math.min(v0,nl.lim)
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
    const look=Math.max(.08,c.v/MPU*.45+.05);
    let tp,ds=c.s+look;
    if(ds>l.len&&nl){const rest=ds-l.len;tp=lanePoint(nl,Math.min(nl.len,rest+.02))}else tp=lanePoint(l,ds);
    const want=Math.atan2(tp[0]-c.x,tp[1]-c.z);let dh=angd(want,c.hd);c.hd=angd(c.hd,0);const maxr=Math.max(.6,c.v/2.7*Math.tan(.55));
    c.hd+=Math.max(-maxr*dt,Math.min(maxr*dt,dh));
    c.x+=Math.sin(c.hd)*c.v/MPU*dt;c.z+=Math.cos(c.hd)*c.v/MPU*dt;
    if(c.s>=l.len-.02&&nl){c.lane=nl;c.s=project(nl,c.x,c.z)[0];c.next=null}
    else if(c.s>=l.len-.02&&!nl){c.stuck+=dt*6}
    if(!nl&&c.v<.3)c.stuck+=dt*2
  }
};
// ---------- colisao com o jogador (3 circulos de cada lado) ----------
T.collide=function(pl){const out={hit:false};
  for(const c of T.cars){const dx=c.x-pl.x,dz=c.z-pl.z;if(Math.abs(dx)>.3||Math.abs(dz)>.3)continue;
    const f=[Math.sin(c.hd),Math.cos(c.hd)],pf=[Math.sin(pl.hd),Math.cos(pl.hd)];
    let best=1e9;for(const a of [-.045,0,.045])for(const b of [-.045,0,.045]){const d=hyp(c.x+f[0]*a-(pl.x+pf[0]*b),c.z+f[1]*a-(pl.z+pf[1]*b));if(d<best)best=d}
    if(best<.07){out.hit=true;out.car=c;out.dx=pl.x-c.x;out.dz=pl.z-c.z;out.rv=hyp(pl.v-c.v*(f[0]*pf[0]+f[1]*pf[1]),0);return out}}
  return out};
// ---------- desenho ----------
T.prepare=function(W3){if(!T.ready&&T.loaded&&W3.ready)validate(W3)};
T.draw=function(W3,pl,t,gy){
  const R=10;
  for(const c of (T.extra?T.cars.concat([T.extra]):T.cars)){
    if(hyp(c.x-pl.x,c.z-pl.z)>R)continue;
    const h=W3.height(c.x,c.z,gy+.025,.06);const y=h===null?gy:h;const ty=c.ty,hl=ty.L/2,w=ty.w/2,hd=c.hd,cl=.014;
    const [r,g,b]=c.col,s=Math.sin(hd),co=Math.cos(hd);
    W3.box(c.x,y+cl+ty.H/2,c.z,hl,ty.H/2,w,hd,r,g,b,0);                                          // carroceria
    const cx=c.x+s*ty.cabOff,cz=c.z+co*ty.cabOff;
    W3.box(cx,y+cl+ty.H+ty.cabH/2,cz,ty.cab/2,ty.cabH/2,w*.88,hd,.08,.11,.17,0);                // vidros
    W3.box(cx,y+cl+ty.H+ty.cabH+.002,cz,ty.cab/2*.92,.002,w*.78,hd,r*.9,g*.9,b*.9,0);           // teto
    for(const fx of [hl*.62,-hl*.62])for(const sd of [-1,1]){                                      // rodas
      W3.box(c.x+s*fx-co*sd*w,y+.012,c.z+co*fx+s*sd*w,.014,.012,.006,hd,.03,.03,.035,0)}
    for(const sd of [-1,1]){                                                                       // farol / lanterna
      W3.box(c.x+s*hl*.99-co*sd*w*.7,y+cl+ty.H*.6,c.z+co*hl*.99+s*sd*w*.7,.003,.005,.01,hd,1,.95,.75,1);
      const br=c.brake>.5;W3.box(c.x-s*hl*.99-co*sd*w*.7,y+cl+ty.H*.6,c.z-co*hl*.99+s*sd*w*.7,.003,.005,.01,hd,br?1:.7,br?.1:.05,br?.1:.05,br?1:.75)}
  }
  // semaforos: poste na calcada, no canto direito de quem chega, antes da faixa de pedestres
  const gx=Math.floor(pl.x/GS),gz=Math.floor(pl.z/GS),rr=Math.ceil(R/GS);
  for(let i=-rr;i<=rr;i++)for(let j=-rr;j<=rr;j++){const arr=grid.get((gx+i)+','+(gz+j));if(!arr)continue;
    for(const n of arr){if(!T.hasLight(n)||hyp(n.x-pl.x,n.z-pl.z)>R+.5)continue;
      for(const l of n.in){const d=l.dir,rt=[-d[1],d[0]],st=T.light(n,l.grp,t);
        if(!l.pole){const bx=n.x-d[0]*l.stop,bz=n.z-d[1]*l.stop;let last=(l.off||.12)+.08;     // anda para a direita ate a borda da rua e coloca o poste na calcada
          for(let k=(l.off||.12)+.1;k<.9;k+=.02){const px=bx+rt[0]*k,pz=bz+rt[1]*k;if(W3.height(px,pz,0,.1)===null||W3.obs(px,pz)||!W3.road(px,pz))break;last=k}
          l.pole=[bx+rt[0]*last,bz+rt[1]*last]}
        const [px,pz]=l.pole,hh=W3.height(px,pz,gy+.2,.2),y=hh===null?gy:hh;
        W3.box(px,y+.09,pz,.003,.09,.003,0,.16,.16,.17,0);                                       // poste ~4,3 m
        const hd=Math.atan2(-d[0],-d[1]);                                                         // cabeca olha para quem chega
        W3.box(px,y+.2,pz,.01,.027,.01,hd,.04,.04,.045,0);                                        // caixa dos focos
        const lamp=(k,col,on)=>W3.box(px-d[0]*.0105,y+.2+k*.017,pz-d[1]*.0105,.0035,.0065,.0065,hd,col[0]*(on?1:.18),col[1]*(on?1:.18),col[2]*(on?1:.18),on?1:0);
        lamp(1,[1,.1,.1],st==='R');lamp(0,[1,.8,.05],st==='Y');lamp(-1,[.1,1,.25],st==='G')}}}
};
T.max=30;T.TYPES=TYPES;
})();
