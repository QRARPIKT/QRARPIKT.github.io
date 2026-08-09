// Qラピカ文库 · 阅读页工具
(function(){
  var root=document.documentElement;
  // 主题
  var saved=localStorage.getItem('qlib-theme');
  if(saved) root.setAttribute('data-theme',saved);
  window.toggleTheme=function(){
    var t=root.getAttribute('data-theme')==='night'?'':'night';
    if(t) root.setAttribute('data-theme',t); else root.removeAttribute('data-theme');
    localStorage.setItem('qlib-theme',t);
  };
  // 字号
  var fs=parseInt(localStorage.getItem('qlib-fs')||'17',10);
  function applyFs(){root.style.setProperty('--font-size',fs+'px');}
  applyFs();
  window.fontSize=function(d){
    fs=Math.min(22,Math.max(14,fs+d));
    localStorage.setItem('qlib-fs',fs); applyFs();
  };
  // 目录抽屉
  window.toggleToc=function(){
    var el=document.getElementById('toc-drawer');
    if(el) el.classList.toggle('open');
  };
})();
