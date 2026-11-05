
(function(){var q=document.getElementById('q');if(!q)return;
var boxes=[].slice.call(document.querySelectorAll('.filters input[type=checkbox]'));
var cards=[].slice.call(document.querySelectorAll('.grid .listing'));var out=document.getElementById('shown');
function run(){var t=q.value.toLowerCase();var zones=boxes.filter(function(b){return b.name=='zone'&&b.checked}).map(function(b){return b.value});
var heavy=document.getElementById('heavy').checked;var n=0;
cards.forEach(function(c){var ok=(!t||c.textContent.toLowerCase().indexOf(t)>-1)&&(zones.length==0||zones.indexOf(c.dataset.zone)>-1)&&(!heavy||c.dataset.heavy=='1');c.style.display=ok?'':'none';if(ok)n++});
out.textContent=n;}
q.addEventListener('input',run);boxes.forEach(function(b){b.addEventListener('change',run)});
var s=document.getElementById('sort');s.addEventListener('change',function(){var g=document.querySelector('.grid');
var arr=cards.slice();if(s.value=='low')arr.sort(function(a,b){return a.dataset.rent-b.dataset.rent});
if(s.value=='high')arr.sort(function(a,b){return b.dataset.rent-a.dataset.rent});
if(s.value=='size')arr.sort(function(a,b){return b.dataset.size-a.dataset.size});arr.forEach(function(c){g.appendChild(c)})});})();
