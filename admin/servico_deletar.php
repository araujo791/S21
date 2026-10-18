<?php include('_topo.php');
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Serviços</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Deletar  serviço</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


";
if($_GET['etapa']=="deletar"){


$cod=$_GET['cod'];


$buscaf = mysql_query("SELECT * FROM servico WHERE id='$cod'",$con);
$row = mysql_fetch_array($buscaf);
$foto1  = $row['fotop'];
$foto2  = $row['fotog'];

@ unlink("../fotos/$foto1");
@ unlink("../fotos/$foto2");


mysql_query("DELETE FROM servico WHERE id=$cod");


echo"<div align='center'>Dados deletados com sucesso! <strong><a href='servico_visualizar.php'>Voltar</a></strong></div>
<br /><br />";

}
else{
$cod=$_GET['cod'];

$busca = mysql_query("SELECT * FROM servico   where id='$cod'");
$row=mysql_fetch_array($busca);
$titulo     = $row['titulo'];



echo"<form name='cadastro'  method='post' action=''>
<input type='hidden'  name='etapa'  value='alterar'>
<input type='hidden'  name='cod'  value='$cod'>

<table border='0' align='center'  width='91%'>

<tr>
<td align='center'>Você deseja deletar o serviço <b>$titulo</b>?<br /><a href='?etapa=deletar&cod=$cod'>Sim</a> - <a href='javascript:history.back(-1);'>Não</a></td>
</tr>
</table>
</form>
";

}

echo"</div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
";
include('_rodape.php');?>
