<?php include('_topo.php');
echo"
<table cellpadding='0' cellspacing='0' width='98%' border='0'>
<tr><td><td width='10'><img src='_imgs/bg_navegacao1l.png'></td><td  id='navegacao_1'>Usuários</td><td  width='10'><img src='_imgs/bg_navegacao1r.png'></td></tr>

<tr><td height='30'>&nbsp;</td></tr>

<tr><td><td width='10'><img src='_imgs/bg_navegacao2l.png'></td><td  id='navegacao_2' valign='top'><div id='navegacao_2_texto'>Adicionar nova usuários</div></td><td  width='10'><img src='_imgs/bg_navegacao2r.png'></td></tr>
</table>

<table cellpadding='0' cellspacing='0' width='98%'>
<tr><td>
<div id='fundo_conteudo'>

<div id='introducao_pgs'>
<br /><br />


";
if($_POST['etapa']=="cadastrar"){

$nome=$_POST['nome'];
$login=$_POST['login'];
$senha=$_POST['senha'];
$email=$_POST['email'];


mysql_query("INSERT INTO usuario (nome,login,senha,email) VALUES ('$nome','$login','$senha','$email')",$con);



echo"<div align='center'>Dados cadastrados com sucesso! <strong><a href='usuario_visualizar.php'>Voltar</a></strong></div>
<br /><br />";

}
else{

echo"<form name='cadastro'  method='post' action=''>
<input type='hidden'  name='etapa'  value='cadastrar'>


<table border='0' align='center'  width='91%'>


<tr>
<td align='right' width='150'>Nome:</td><td align='right'><input name='nome'  type='text' class='class_inputs'></td>
</tr>
<tr>
<td align='right' width='150'>E-mail:</td><td align='right'><input name='email'  type='text' class='class_inputs'></td>
</tr>
<tr>
<td align='right' width='150'>Usuário:</td><td align='right'><input name='login'  type='text' class='class_inputs'></td>
</tr>
<tr>
<td align='right' width='150'>Senha:</td><td align='right'><input name='senha'  type='password' class='class_inputs'></td>
</tr>


<tr>
<td align='right' colspan='2'><div style='margin-right:1px;'><input type='image' src='_imgs/bt_cadastrar.png'></div></td>
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
