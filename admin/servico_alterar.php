<?php include('_topo.php');?>
<script type='text/javascript' src='ckeditor/ckeditor.js'></script>
<script src='ckeditor/_samples/sample.js' type='text/javascript'></script>

<?php
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Serviços</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Alterar  serviço</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


";
if($_POST['etapa']=="alterar"){

$cod          = $_POST['cod'];

$titulo       = $_POST['titulo'];
$descricao    = $_POST['descricao'];
$categoria    = $_POST['categoria'];

mysql_query ("UPDATE servico SET titulo='$titulo',descricao='$descricao',categoria='$categoria' WHERE id='$cod'",$con);

$data            =     date('Y-m-d-H-i-s');

if($_FILES["imagem1"]["name"]!=""){

ini_set("memory_limit","90M");

require( 'canvas.php' );

$imagem_name=$_FILES["imagem1"]["name"];
$imagem=$_FILES["imagem1"]["tmp_name"];

$explode = explode(".", $imagem_name);
$foto = $explode[count($explode) - 1];


$nome_img_p ="fotos-$data-p.$foto";
$nome_img_g ="fotos-$data-g.$foto";


$img = new canvas();
$img->carrega($imagem)
->redimensiona( 480, 420, 'crop' )
	->grava("../fotos/$nome_img_p");

$img = new canvas();
$img->carrega($imagem)
 ->redimensiona( 800 )
	->grava("../fotos/$nome_img_g");



$buscaf = mysql_query("SELECT * FROM servico WHERE id='$cod'",$con);
$row = mysql_fetch_array($buscaf);
$foto1  = $row['fotop'];
$foto2  = $row['fotog'];

@ unlink("../fotos/$foto1");
@ unlink("../fotos/$foto2");


mysql_query ("UPDATE servico SET fotop='$nome_img_p',fotog='$nome_img_g' WHERE id='$cod'",$con);

}



echo"<div align='center'>Dados alterados com sucesso! <strong><a href='servico_visualizar.php'>Voltar</a></strong></div>
<br /><br />";

}
else{
$cod=$_GET['cod'];

$busca = mysql_query("SELECT * FROM servico   where id='$cod'");
$row=mysql_fetch_array($busca);
$titulo       = $row['titulo'];
$descricao    = $row['descricao'];
$imagem       = $row['fotop'];
$categoria    = $row['categoria'];

echo"<form name='cadastro'  method='post' action='' enctype='multipart/form-data'>
<input type='hidden'  name='etapa'  value='alterar'>
<input type='hidden'  name='cod'  value='$cod'>

<table border='0' align='center'  width='91%'>




<tr>
<td align='right' width='150'>Título:</td><td align='right'><input name='titulo' type='text' value='$titulo' class='class_inputs'></td>
</tr>

<tr>
<td align='right' width='150'>Descrição:</td><td align='right'>";
?>
		<textarea  id="descricao" name="descricao" rows="10"  class='class_inputs'><?php echo $descricao; ?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'descricao',
 {
 filebrowserBrowseUrl : 'ckeditor/ckfinder/ckfinder.html',
 filebrowserImageBrowseUrl : 'ckeditor/ckfinder/ckfinder.html?Type=Images',
 filebrowserFlashBrowseUrl : 'ckeditor/ckfinder/ckfinder.html?Type=Flash',
 filebrowserUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Files',
 filebrowserImageUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Images',
 filebrowserFlashUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Flash'
 });
</script>
<?php echo"</td>
</tr>


<tr>
<td align='right' width='150'>Imagem:</td><td align='right'><input name='imagem1'  type='file' class='class_inputs'></td>
</tr>



<tr>
<td align='right' colspan='2'><div style='margin-right:1px;'><input type='image' src='_imgs/bt_alterar.png'></div></td>
</tr>
</table>
</form>
";
echo"<div align='center'><img src='../fotos/$imagem' width='650' /></div>";
}

echo"</div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
";
include('_rodape.php');?>
