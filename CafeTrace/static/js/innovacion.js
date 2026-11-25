(()=>{'use strict';
const chat=document.getElementById('ct-chat'),form=document.getElementById('ct-form'),input=document.getElementById('ct-input'),mic=document.getElementById('ct-mic');
if(!form)return;
const endpoint='/api/asistente/';
function add(text,kind,url,label){let d=document.createElement('div');d.className='ct-msg '+kind;d.textContent=text;if(url&&url.startsWith('/')){let b=document.createElement('div'),a=document.createElement('a');a.href=url;a.textContent=label||'Abrir herramienta';b.appendChild(a);d.appendChild(b);}chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
async function send(q){if(!q.trim())return;add(q,'user');input.value='';try{let r=await fetch(endpoint+'?q='+encodeURIComponent(q),{headers:{'Accept':'application/json'},credentials:'same-origin'});if(!r.ok)throw Error('No se pudo consultar el servidor');let j=await r.json();add(j.respuesta,'bot',j.url,j.etiqueta);}catch(e){add('No pude consultar CaféTrace. Verifica que el servidor esté activo y que tu sesión siga abierta.','bot');}}
form.addEventListener('submit',e=>{e.preventDefault();send(input.value)});
document.querySelectorAll('[data-query]').forEach(b=>b.addEventListener('click',()=>send(b.dataset.query)));
const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(!Recognition){mic.disabled=true;mic.title='Este navegador no ofrece dictado de voz';document.getElementById('ct-voice-note').textContent='Tu navegador no ofrece reconocimiento de voz. Puedes utilizar el campo de texto.';return;}
mic.addEventListener('click',()=>{let r=new Recognition();r.lang='es-EC';r.interimResults=false;r.maxAlternatives=1;mic.textContent='●';r.onresult=e=>{let transcript=e.results[0][0].transcript;input.value=transcript;
let t=transcript.toLocaleLowerCase('es');
const rutas=[['abrir almacén','/areas/almacen/'],['abrir almacen','/areas/almacen/'],['ir a almacén','/areas/almacen/'],['abrir producción','/areas/produccion/'],['abrir distribucion','/areas/distribucion/'],['abrir distribución','/areas/distribucion/'],['abrir tienda','/areas/tienda/'],['abrir catálogo','/catalogo/'],['abrir catalogo','/catalogo/'],['abrir qr','/tienda/qr/']];
let par=rutas.find(x=>t.includes(x[0]));
if(par){add('Comando de voz: '+transcript,'user');add('Abriendo la sección solicitada.','bot',par[1],'Abrir');window.location.assign(par[1]);}
else{send(transcript)}};r.onerror=()=>{document.getElementById('ct-voice-note').textContent='No se pudo reconocer la voz. Revisa el permiso del micrófono.'};r.onend=()=>{mic.textContent='🎙'};r.start();});
})();
