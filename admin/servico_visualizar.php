<?php include('_topo.php');
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Serviços</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Serviços encontrados</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


<form name=''  method='get' action=''>
<table border='0' align='center'  width='91%' id='tables'><tr>
<td width='30'  align='left'><b>Título</b>:</td>
<td align='left'><input name='titulo_busca'  type='text' class='class_inputs'></td>
<td width='130' align='right'><input type='image' src='_imgs/bt_buscar.png'></td>
</tr>
</table>
</form>
<br /><br />


<table border='0' align='center'  width='91%' id='tables'>

<tr bgcolor='#dedede'>
<td><strong>Título</strong></td><td  align='center'><strong>Ações</strong></td>
</tr>
";

if($_REQUEST['titulo_busca']!=""){$titulo_busca=" WHERE titulo LIKE '%".$_REQUEST['titulo_busca']."%' ";}else{$titulo_busca="";}

$y=0;
$busca = mysql_query("SELECT * FROM servico  $titulo_busca  order by titulo ASC");
$total_busca = mysql_num_rows($busca);
while($row=mysql_fetch_array($busca)){
$y++;
$titulo       = $row['titulo'];
$data         = $row['data'];
$categoria    = $row['categoria'];
$cod          = $row['id'];

if(($y % 2) == 1){$fundo="#ffffff";}else{$fundo="#EBEBEB";}

if($destaque=="1"){$destaque="Sim";}else{$destaque="Não";}


echo"
<tr  bgcolor='$fundo'>
<td>$titulo</td><td width='50' align='center'><a href='servico_alterar.php?cod=$cod'><img src='_imgs/ico_alterar.gif' border='0'></a> <a href='servico_deletar.php?cod=$cod'><img src='_imgs/ico_deletar.gif' border='0'></a></td>
</tr>
";

}

echo"
</table>

";

if($total_busca=="0"){echo"<br /><br /><div align='center'>Nenhum resultado encontrado.</div><br /><br /><br /><br />";}


echo"

</div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
";
include('_rodape.php');?>
