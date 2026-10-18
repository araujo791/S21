<?php include('_topo.php');?>

<script type="text/javascript" src="_scripts/jquery-latest.js"></script>
<script type="text/javascript" src="_scripts/jquery.tablesorter.js"></script>


<script>

$(function(){
  $("table").tablesorter({widgets: ['zebra'],
    headers: {
      1: { sorter: false },
    }
  });
});
</script>

<style>
 /* TABELA COR SIM COR NAO */
th{
padding:3px;
margin:0;
text-align:left;
}
table.tablesorter thead tr .header {
	background-image: url(_imgs/bg.gif);
	background-repeat: no-repeat;
	background-position: center right;
	cursor: pointer;
}



.tablesorter tbody tr {

	background-color: #EBEBEB;

}
.tablesorter tbody tr.odd  {
	background-color:#ffffff;
}

table.tablesorter thead tr .headerSortUp {
	background-image: url(_imgs/asc.gif);
}
table.tablesorter thead tr .headerSortDown {
	background-image: url(_imgs/desc.gif);
}


 /*FIM TABELA COR SIM COR NAO */
</style>

<?php
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Páginas</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Consultar páginas</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
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


<table border='0' align='center'  width='91%' id='tables' class='tablesorter'>
<thead>
<tr bgcolor='#dedede'>
<th><strong>Título</strong></th>
<th><div align='center'><strong>Ações</strong></div></th>
</tr></thead><tbody>
";


if($_REQUEST['titulo_busca']!=""){$titulo_busca=" AND titulo LIKE '%".$_REQUEST['titulo_busca']."%' ";}else{$titulo_busca="";}

$y=0;
$busca = mysql_query("SELECT * FROM pagina   $titulo_busca order by ordem asc,titulo asc");
$total_busca = mysql_num_rows($busca);
while($row=mysql_fetch_array($busca)){
$y++;
$titulo  = $row['titulo'];
$cod     = $row['id'];


if(($y % 2) == 1){$fundo="#ffffff";}else{$fundo="#EBEBEB";}

echo"
<tr  bgcolor='$fundo'>
<td>$titulo</td><td width='50' align='center'><a href='pagina_alterar.php?cod=$cod'><img src='_imgs/ico_alterar.gif' border='0'></a></td>
</tr>
";
}



echo"
</tbody></table>
";

if($total_busca=="0"){echo"<tr><td><br /><br /><div align='center'>Nenhum resultado encontrado.</div><br /><br /></td></tr>";}

echo"


</div>
</div></td></tr>
</table>
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td><img src='_imgs/bg_navegacao1l.png' style='margin-left:3px;'></td><td width='100%'><div   id='navegacao_1'>&nbsp;</div></td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>
</table>
";
include('_rodape.php');?>
