<?php include('_topo.php');?>
<script type='text/javascript' src='ckeditor/ckeditor.js'></script>
<script src='ckeditor/_samples/sample.js' type='text/javascript'></script>

<?php
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Páginas</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Alterar página</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


";
if($_POST['etapa']=="alterar"){

$titulo  =  $_POST['titulo'];
$texto1  =  $_POST['texto1'];
$texto2  =  $_POST['texto2'];
$texto3  =  $_POST['texto3'];
$texto4  =  $_POST['texto4'];
$texto5  =  $_POST['texto5'];
$texto6  =  $_POST['texto6'];
$texto7  =  $_POST['texto7'];
$texto8  =  $_POST['texto8'];
$texto9  =  $_POST['texto9'];
$texto10  =  $_POST['texto10'];
$texto11  =  $_POST['texto11'];
$texto12  =  $_POST['texto12'];

$cod     =  $_POST['cod'];

mysql_query ("UPDATE pagina SET texto6='$texto6',texto7='$texto7',texto8='$texto8',texto9='$texto9',texto10='$texto10',texto11='$texto11',texto12='$texto12',texto1='$texto1',texto2='$texto2',texto3='$texto3',texto4='$texto4',texto5='$texto5' WHERE id='$cod'",$con);



echo"<div align='center'>Dados alterados com sucesso! <strong><a href='index.php'>Voltar</a></strong></div>
<br /><br />";

}
else{
$cod=$_GET['cod'];

$busca = mysql_query("SELECT * FROM pagina   where id='$cod'");
$row=mysql_fetch_array($busca);
$titulo  = $row['titulo'];
$texto1  = $row['texto1'];
$texto2  = $row['texto2'];
$texto3  = $row['texto3'];
$texto4  = $row['texto4'];
$texto5  = $row['texto5'];
$texto6  =  $row['texto6'];
$texto7  =  $row['texto7'];
$texto8  =  $row['texto8'];
$texto9  =  $row['texto9'];
$texto10  =  $row['texto10'];
$texto11  =  $row['texto11'];
$texto12  =  $row['texto12'];


echo"<form name='cadastro'  method='post' action=''>
<input type='hidden'  name='etapa'  value='alterar'>
<input type='hidden'  name='cod'  value='$cod'>

<table border='0' align='center'  width='91%'>


<tr>
<td align='right' width='150'>Página:</td><td align='left'><strong>$titulo</strong></td>
</tr>

";

if($cod=="5"){

echo"


<tr>
<td align='right' width='150'>Endereço:</td><td align='right'><input name='texto1' type='text' value='$texto1' class='class_inputs'></td>
</tr>



";

}else{

echo"
<tr>
<td align='right' width='150'>Texto 1:</td><td align='right'>";
?>
		<textarea  id="texto1" name="texto1" rows="10"  class='class_inputs'><?php echo"$texto1";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto1',
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
";

if($cod=="1"){


echo"
<tr>
<td align='right' width='150'>Texto 2:</td><td align='right'>";
?>
		<textarea  id="texto2" name="texto2" rows="10"  class='class_inputs'><?php echo"$texto2";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto2',
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
<td align='right' width='150'>Texto 3:</td><td align='right'>";
?>
		<textarea  id="texto3" name="texto3" rows="10"  class='class_inputs'><?php echo"$texto3";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto3',
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
<td align='right' width='150'>Texto 4:</td><td align='right'>";
?>
		<textarea  id="texto4" name="texto4" rows="10"  class='class_inputs'><?php echo"$texto4";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto4',
 {
 filebrowserBrowseUrl : 'ckeditor/ckfinder/ckfinder.html',
 filebrowserImageBrowseUrl : 'ckeditor/ckfinder/ckfinder.html?Type=Images',
 filebrowserFlashBrowseUrl : 'ckeditor/ckfinder/ckfinder.html?Type=Flash',
 filebrowserUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Files',
 filebrowserImageUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Images',
 filebrowserFlashUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Flash'
 });
</script>
<?echo"</td>
</tr>

<tr>
<td align='right' width='150'>Texto 5:</td><td align='right'>";
?>
		<textarea  id="texto5" name="texto5" rows="10"  class='class_inputs'><?php echo"$texto5";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto5',
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
<td align='right' width='150'>Texto 6:</td><td align='right'>";
?>
		<textarea  id="texto6" name="texto6" rows="10"  class='class_inputs'><?php echo"$texto6";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto6',
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
<td align='right' width='150'>Texto 7:</td><td align='right'>";
?>
		<textarea  id="texto7" name="texto7" rows="10"  class='class_inputs'><?php echo"$texto7";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto7',
 {
 filebrowserBrowseUrl : 'ckeditor/ckfinder/ckfinder.html',
 filebrowserImageBrowseUrl : 'ckeditor/ckfinder/ckfinder.html?Type=Images',
 filebrowserFlashBrowseUrl : 'ckeditor/ckfinder/ckfinder.html?Type=Flash',
 filebrowserUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Files',
 filebrowserImageUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Images',
 filebrowserFlashUploadUrl : 'ckeditor/ckfinder/core/connector/php/connector.php?command=QuickUpload&type=Flash'
 });
</script>
<?echo"</td>
</tr>
";




}



if($cod=="4"){


echo"
<tr>
<td align='right' width='150'>Texto 2:</td><td align='right'>";
?>
		<textarea  id="texto2" name="texto2" rows="10"  class='class_inputs'><?php echo"$texto2";?></textarea>
<script type="text/javascript">
CKEDITOR.replace( 'texto2',
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


";




}

}



echo"
<tr>
<td align='right' colspan='2'><div style='margin-right:1px;'><input type='image' src='_imgs/bt_alterar.png'></div></td>
</tr>
</table>
</form>
";

if(($cod==3)){
echo"<br /><br />";

$busca = mysql_query("SELECT * FROM pagina_foto WHERE local='$cod'  order by id asc");
$total = mysql_num_rows($busca);
while($row=mysql_fetch_array($busca)){
$fotop    = $row['fotop'];
$codFoto  = $row['id'];
$pagina   = $row['local'];


echo"<div align='center'><img src='../fotos/$fotop' width='200' /><br /><a href='pagina_foto_alterar.php?cod=$codFoto'><strong>Alterar</strong></a></div><br />";

}

}


}

echo"</div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
";
include('_rodape.php');?>
