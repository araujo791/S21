//*************************************************************************
// fdButton - Desenvolvido por Fabiano Dias - contatofd@gmail.com
//*************************************************************************
// Evita o refresh dos backgrounds no IE
(function(){
var m = document.uniqueID
&& document.compatMode
&& !window.XMLHttpRequest
&& document.execCommand ;
try{if(!!m){m("BackgroundImageCache", false, true)}}catch(oh){};
})();
var fdButton_Clicked = null;
//*************************************************************************
// EVENTOS DO MOUSE SOBRE AS ButtonS
//*************************************************************************
function fdButton_Over(obj){
  if(obj.className!="fdButtonRightClick"){
    if(obj.className!="fdButtonRightDisabled"){
      obj.className="fdButtonRightOver";
      obj.getElementsByTagName('div')[0].className="fdButtonLeftOver";
    }
  }
}
function fdButton_Out(obj){
  if(obj.className!="fdButtonRightDisabled"){
    obj.className="fdButtonRight";
    obj.getElementsByTagName('div')[0].className="fdButtonLeft";
  }
}
function fdButton_MouseDown(obj, id){
  if(obj.className!="fdButtonRightDisabled"){
    var objId = document.getElementById(id).getElementsByTagName('div');
    for(x=0; x<=objId.length-1; x = x + 2){
      if(objId[x].className=="fdButtonRightClick"){
        objId[x].className = 'fdButtonRight';
        objId[x+1].className = 'fdButtonLeft';
      }
    }
    obj.className="fdButtonRightClick";
    obj.getElementsByTagName('div')[0].className="fdButtonLeftClick";
  }
}
function fdButton_Click(obj, id){
  if(obj.className!="fdButtonRightDisabled"){
	fdButton_Out(obj);
    fdButton_Clicked = id;
    fdButtonClicked();
  }
}
//*************************************************************************
// FUNCOES PARA MANIPULAÇÃO DAS ButtonS
//*************************************************************************
function fdButton_setButtonDisabled(id){
  var obj = document.getElementById(id).getElementsByTagName('div');
  obj[0].className = 'fdButtonRightDisabled';
  obj[1].className = 'fdButtonLeftDisabled';
  var obj = obj[0].getElementsByTagName('img');
  if (obj[0]){
    obj[0].style.filter='Alpha(Opacity=30);';
    obj[0].style.MozOpacity='.30';
  }
}
function fdButton_setButtonEnabled(id){
  var obj = document.getElementById(id).getElementsByTagName('div');
  obj[0].className = 'fdButtonRight';
  obj[1].className = 'fdButtonLeft';
  var obj = obj[0].getElementsByTagName('img');
  if (obj[0]){
    obj[0].style.filter='';
    obj[0].style.MozOpacity='';
  }
}
function fdButton_setButtonHidden(id){
  var obj = document.getElementById(id).getElementsByTagName('div');
  obj[0].style.display='none';
}
function fdButton_setButtonDisplay(id){
  var obj = document.getElementById(id).getElementsByTagName('div');
  obj[0].style.display='';
}
//*************************************************************************
// FUNÇÃO PARA CRIAÇÃO DO BOTÃO
//*************************************************************************
function fdButton_Create(id, titulo, icon){
  var text = '';
  text = text + '<div id="'+id+'" class="fdButton">';
  text = text + '  <div><div>';
  if (icon!='') text = text + '<img src="icons/'+icon+'" align="absmiddle" width="14" height="14">';
  text = text + titulo + '</div></div>';
  text = text + '</div>';
  document.write(text)
  var obj = document.getElementById(id).getElementsByTagName('div');
  for(x=0; x<=obj.length-1; x = x + 2){
    obj[x].id = (x/2)+1;
    obj[x].className = 'fdButtonRight';
    obj[x+1].className = 'fdButtonLeft';
    obj[x].onmouseover = function(){fdButton_Over(this)};
    obj[x].onmouseout = function(){fdButton_Out(this)};
    obj[x].onclick = function(){fdButton_Click(this, id);};
	obj[x].onmousedown = function () { fdButton_MouseDown(this, id); return false; }; // mozilla
	obj[x].onselectstart = function () { return false; }; // ie
  }
}
//*************************************************************************