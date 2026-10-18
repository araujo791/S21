<?php include('_topo.php');require('canvas.php');

echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Páginas</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Alterar foto</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


";
if($_POST['etapa']=="alterar"){

$cod     = $_POST['cod'];

if($_FILES["imagem"]["name"]!=""){
$data=date('Y-m-d-H-i-s');

$imagem_name=$_FILES["imagem"]["name"];
$imagem=$_FILES["imagem"]["tmp_name"];

$explode = explode(".", $imagem_name);
$ext= $explode[count($explode) - 1];


$nome_imgp="fotos-p-$data.$ext";
$nome_imgg="fotos-g-$data.$ext";

$busca_foto2 = mysql_query("SELECT * FROM pagina_foto   where id='$cod'");
$row=mysql_fetch_array($busca_foto2);
$fotop          = $row['fotop'];
$fotom          = $row['fotom'];
$fotog          = $row['fotog'];
$pagina         = $row['local'];



$img = new canvas();
$img->carrega($imagem)
	->redimensiona( 960, 593, 'crop' )
	->grava("../fotos/$nome_imgp");



$img = new canvas();
$img->carrega($imagem)
	->redimensiona( 800 )
	->grava("../fotos/$nome_imgg");


@ unlink("../fotos/$fotop");
@ unlink("../fotos/$fotog");


mysql_query ("UPDATE pagina_foto SET fotop='$nome_imgp',fotog='$nome_imgg' WHERE id='$cod'",$con);
}



echo"<div align='center'>Dados alterados com sucesso! <strong><a href='pagina_alterar.php?cod=$pagina'>Voltar</a></strong></div>
<br /><br />";

}
else{
$cod=$_GET['cod'];

$busca = mysql_query("SELECT * FROM pagina_foto   where id='$cod'");
$row=mysql_fetch_array($busca);
$foto       = $row['fotop'];
$pagina     = $row['local'];



$tamanho=" (300x160px)";




echo"<form name='cadastro'  method='post' action='' enctype='multipart/form-data'>
<input type='hidden'  name='etapa'  value='alterar'>
<input type='hidden'  name='cod'  value='$cod'>


<table border='0' align='center'  width='91%'>



<tr><td align='right'>Foto:</td><td align='left'><div style='padding-left:4px;'><input type='file' name='imagem'  size='50'></div></td></tr>



<tr><td align='right' colspan='2'><input type='image' src='_imgs/bt_alterar.png'></td></tr></table>
</form>
<br /><br />";

echo"<div align='center'><img src='../fotos/$foto' width='300' /></div>";
}

echo"</div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
";
include('_rodape.php');?>
