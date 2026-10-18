<?php session_start();include('bd.php');
$busca = mysql_query("SELECT * FROM usuario   where id='$_SESSION[LOGIN]'");
$total = mysql_num_rows($busca);
if($total=="0"){header("location: login.php");}
?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
<title>Sistema administrativo</title>
<link href="_css/css.css" rel="stylesheet" type="text/css">

<script language="javascript">
function abre_menu_left(){
	expandTree('tree1');
	expandTree('tree2');
	expandTree('tree3');
	expandTree('tree4');
	expandTree('tree5');
	expandTree('tree6');
	expandTree('tree7');
	expandTree('tree8');
	expandTree('tree9');
	expandTree('tree10');
	expandTree('tree11');
	expandTree('tree12');
	expandTree('tree13');
	expandTree('tree14');
	expandTree('tree15');
    expandTree('tree16');
    expandTree('tree17');
    expandTree('tree18');
    expandTree('tree19');
    expandTree('tree20');
    expandTree('tree21');
	return false;
	}
 function fecha_menu_left(){
	collapseTree('tree1');
	collapseTree('tree2');
	collapseTree('tree3');
	collapseTree('tree4');
	collapseTree('tree5');
	collapseTree('tree6');
	collapseTree('tree7');
	collapseTree('tree8');
	collapseTree('tree9');
	collapseTree('tree10');
	collapseTree('tree11');
	collapseTree('tree12');
	collapseTree('tree13');
	collapseTree('tree14');
	collapseTree('tree15');
    collapseTree('tree16');
    collapseTree('tree17');
    collapseTree('tree18');
    collapseTree('tree19');
    collapseTree('tree20');
    collapseTree('tree21');
	return false;
}</script>

<script language="javascript" src="_scripts/mktree.js"></script>
<script src="_scripts/AC_RunActiveContent.js" type="text/javascript"></script>

<link href="_css/menu.css" rel="stylesheet" type="text/css">
</head>


<?
$ArrPATH = explode("/",$_SERVER['SCRIPT_NAME']);

$PATH = $ArrPATH[count($ArrPATH)-1];

if(($PATH=="pagina_alterar.php") || ($PATH=="index.php") || ($PATH=="pagina_foto_alterar.php")){echo"<body onload=\"expandTree('tree3');\">";}
elseif(($PATH=="servico_visualizar.php") || ($PATH=="servico_deletar.php") || ($PATH=="servico_cadastrar.php") || ($PATH=="servico_alterar.php")){echo"<body onload=\"expandTree('tree8');\">";}
elseif(($PATH=="banner_visualizar.php") || ($PATH=="banner_deletar.php") || ($PATH=="banner_cadastrar.php") || ($PATH=="banner_alterar.php")){echo"<body onload=\"expandTree('tree6');\">";}
elseif(($PATH=="usuario_cadastrar.php") || ($PATH=="usuario_alterar.php") || ($PATH=="usuario_visualizar.php") || ($PATH=="usuario_deletar.php")){echo"<body onload=\"expandTree('tree15');\">";}



else{echo"<body>";}
?>

<div id="topo">
<table class="topo" style="padding-right:3px;" align="center" border="0" cellpadding="0" cellspacing="0" width="97%"><tbody><tr>
<td align="left" valign="top"><a href="index.php"><img src="_imgs/logo.png" border="0"></a></td>
<td class="botao" align="left" valign="top" width="150"></td>
<td class="botao" align="center" valign="top" width="150"><a href="index.php"><img src="_imgs/bt_inicio.png" border="0"></a></td>
<td class="botao" align="right" valign="top" width="140"><a href="usuario_visualizar.php"><img src="_imgs/bt_usuarios.png" border="0"></a></td>
</tr>
<?
$busca = mysql_query("SELECT * FROM usuario   where id='$_SESSION[LOGIN]'");
$row=mysql_fetch_array($busca);
$nome_topo  = $row['nome'];
?>
<tr><td colspan="4" valign="top" align="right">Ol&aacute; <strong><?echo"$nome_topo";?></strong> | <a href="login.php">Sair</a></td></tr></table>
</div>
<table cellpadding="0" cellspacing="0" width="100%" border="0" align="center"  class="topo"><tr><td id="menu_left" valign="top">
<div id="menu_left_texto">
	  <div align="center"><a href="javascript:;" onClick="abre_menu_left();">Expandir todos</a> -
	  <a href="javascript:;" onClick="fecha_menu_left();">Recolher todos</a></div>
<br />




 <ul class='mktree' id='tree3' style='margin:2px; padding:2px;'>
        <li>P&aacute;ginas informativas<br />
  <img src="_imgs/menu_linha.png" width="183" height="2" vspace="10"  /><br />
          <ul><li><a href='index.php'>Consultar páginas</a></li><img src="_imgs/menu_linha.png" width="160" height="2" vspace="10"  style="margin-left:22px;" /><br />
 </ul></li></ul>

      <ul class='mktree' id='tree8' style='margin:2px; padding:2px;'>
        <li>Serviços<br />
  <img src="_imgs/menu_linha.png" width="183" height="2" vspace="10"  /><br />
          <ul>
<li><a href='servico_visualizar.php'>Consultar serviços</a></li>
            <img src="_imgs/menu_linha.png" width="160" height="2" vspace="10"  style="margin-left:22px;" /><br />
            <li><a href='servico_cadastrar.php'>Adicionar serviços</a></li>  <img src="_imgs/menu_linha.png" width="160" height="2" vspace="10"  style="margin-left:22px;" /><br />

</ul></li></ul>


<ul class='mktree' id='tree15' style='margin:2px; padding:2px;'>
        <li>Administradores<br />
  <img src="_imgs/menu_linha.png" width="183" height="2" vspace="10"  /><br />
          <ul><li><a href='usuario_visualizar.php'>Consultar usuários</a></li>
            <img src="_imgs/menu_linha.png" width="160" height="2" vspace="10"  style="margin-left:22px;" />
          <br />
            <li><a href='usuario_cadastrar.php'>Adicionar usuários</a></li>  <img src="_imgs/menu_linha.png" width="160" height="2" vspace="10"  style="margin-left:22px;" /><br />



</ul></li></ul>
</div>
</td><td valign="top">
