<?php session_start();include('bd.php'); ?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
<title>Sistema administrativo da loja</title>
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
	return false;
}</script>

<script language="javascript" src="_scripts/mktree.js"></script>
<script src="_scripts/AC_RunActiveContent.js" type="text/javascript"></script>

<link href="_css/menu.css" rel="stylesheet" type="text/css">
</head>

<body style='background-image: url(_imgs/x.gif);'>


<div id="topo">
<table cellpadding="0" cellspacing="0" width="97%" border="0" align="center"  class="topo" style='padding-right:3px;'><tr>
<td  valign="top" align="left"><a href='index.php'><img src="_imgs/logo.png"  border='0'  /></a></td>
</tr>
</table>
</div>
<table cellpadding="0" cellspacing="0" width="100%" border="0" align="center"  class="topo"><tr><td width='20'>&nbsp;</td>
<td valign="top">
<?
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Login</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Preencha os dados para entrar no sistema.</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


";

if($_POST['etapa']=="cadastrar"){


$login=$_POST['login'];
$senha=$_POST['senha'];



$busca = mysql_query("SELECT * FROM usuario WHERE login='$login' AND senha='$senha'",$con);
$total = mysql_num_rows($busca);
$row=mysql_fetch_array($busca);
$id = $row['id'];

if($total>="1"){$_SESSION['LOGIN']=$id;?>
 <script language="JavaScript">
 location.href="<?echo"index.php";?>"
 </script><?}else{

?>
 <script language="JavaScript">
 alert("Usuário/Senha incorretos!");
 location.href="<?echo"login.php";?>"
 </script><?
 }
 

}
else{
unset($_SESSION['LOGIN']);
echo"<form name='cadastro'  method='post' action=''>
<input type='hidden'  name='etapa'  value='cadastrar'>


<table border='0' align='center'  width='91%'>



<tr>
<td align='right' width='150'>Usuário:</td><td align='right'><input name='login'  type='text' class='class_inputs'></td>
</tr>
<tr>
<td align='right' width='150'>Senha:</td><td align='right'><input name='senha'  type='password' class='class_inputs'></td>
</tr>


<tr>
<td align='right' colspan='2'><div style='margin-right:1px;'><input type='image' src='_imgs/bt_entrar.png'></div></td>
</tr>
</table>
</form>
";

}

echo"<div style='cleat:both;'></div><div style='height:150px;'></div></div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
<div style='cleat:both;'></div><div style='height:150px;'></div>";
include('_rodape.php');?>
