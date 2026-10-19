<?php
declare(strict_types=1);

header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Content-Security-Policy: default-src \'none\'; base-uri \'none\'; frame-ancestors \'none\'');

function respond(int $status, string $message, array $extra = []): void
{
    http_response_code($status);
    if (strpos($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json') !== false) {
        header('Content-Type: application/json; charset=UTF-8');
        echo json_encode(array_merge(['ok' => $status < 400, 'message' => $message], $extra), JSON_UNESCAPED_UNICODE);
    } else {
        header('Content-Type: text/html; charset=UTF-8');
        echo '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Contato S21</title><body><h1>Contato S21</h1><p>'
            . htmlspecialchars($message, ENT_QUOTES, 'UTF-8')
            . '</p><p><a href="index.html#contato">Voltar ao site</a></p></body></html>';
    }
    exit;
}

if (!in_array($_SERVER['REQUEST_METHOD'] ?? '', ['GET', 'POST'], true)) {
    header('Allow: GET, POST');
    respond(405, 'Método não permitido.');
}
if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 40000) {
    respond(413, 'Mensagem muito longa. Reduza o texto e tente novamente.');
}
ini_set('session.use_strict_mode', '1');
session_name('s21_contact');
session_set_cookie_params([
    'httponly' => true,
    'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
    'samesite' => 'Strict',
    'path' => '/',
]);
if (!session_start()) {
    respond(503, 'Contato indisponível no momento. Ligue para 0800 878 21 77.');
}
if (empty($_SESSION['contact_token'])) {
    $_SESSION['contact_token'] = bin2hex(random_bytes(32));
}
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    respond(200, 'Formulário disponível.', ['token' => $_SESSION['contact_token']]);
}
$token = $_POST['token'] ?? '';
if (!is_string($token) || !hash_equals($_SESSION['contact_token'], $token)) {
    respond(403, 'Sua sessão expirou. Atualize a página e tente novamente.');
}
function field(string $name, int $max, bool $required = true): string
{
    $value = $_POST[$name] ?? '';
    if (!is_string($value) || !preg_match('//u', $value)) {
        respond(422, 'Revise os campos do formulário.');
    }
    $value = trim($value);
    $length = preg_match_all('/./us', $value);
    if (($required && $value === '') || $length > $max || strpos($value, "\0") !== false) {
        respond(422, 'Revise os campos obrigatórios e os limites de tamanho.');
    }
    return $value;
}
if (field('website', 200, false) !== '') {
    respond(422, 'Não foi possível validar este contato. Ligue para nossa central.');
}
$name = field('nome', 120);
$company = field('empresa', 160, false);
$email = field('email', 254);
$phone = field('telefone', 30);
$subject = field('assunto', 100);
$message = field('mensagem', 5000);
$subjects = ['Informações sobre serviços', 'Plano de Atendimento a Emergências', 'Treinamentos e simulados', 'Área de atuação', 'Outros assuntos'];
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || preg_match('/[\r\n]/', $email)
    || !in_array($subject, $subjects, true) || ($_POST['consentimento'] ?? null) !== '1'
    || strlen(preg_replace('/\D/', '', $phone)) < 8) {
    respond(422, 'Informe um e-mail e telefone válidos, escolha o assunto e autorize o contato.');
}
// Limite por IP: 5 tentativas válidas em 15 minutos. Não armazena os dados do formulário.
$ratePath = sys_get_temp_dir() . '/s21-contact-' . hash('sha256', __DIR__ . ($_SERVER['REMOTE_ADDR'] ?? 'unknown')) . '.json';
$rate = @fopen($ratePath, 'c+');
if (!$rate || !flock($rate, LOCK_EX)) {
    respond(503, 'Contato indisponível no momento. Tente mais tarde ou ligue para nossa central.');
}
$attempts = json_decode(stream_get_contents($rate), true);
$attempts = is_array($attempts) ? array_values(array_filter($attempts, static function ($time) {
    return is_int($time) && $time > time() - 900;
})) : [];
if (count($attempts) >= 5) {
    flock($rate, LOCK_UN);
    fclose($rate);
    header('Retry-After: 900');
    respond(429, 'Muitas tentativas. Aguarde 15 minutos ou ligue para nossa central.');
}
$attempts[] = time();
$encodedAttempts = json_encode($attempts);
$written = ftruncate($rate, 0) && rewind($rate) && fwrite($rate, $encodedAttempts) === strlen($encodedAttempts) && fflush($rate);
flock($rate, LOCK_UN);
fclose($rate);
if (!$written) {
    respond(503, 'Contato indisponível no momento. Ligue para nossa central.');
}
$config = require __DIR__ . '/contato-config.php';
foreach (['recipient', 'sender'] as $key) {
    if (!isset($config[$key]) || !is_string($config[$key]) || !filter_var($config[$key], FILTER_VALIDATE_EMAIL)
        || preg_match('/[\r\n]/', $config[$key])) {
        error_log('S21: configuração de e-mail inválida.');
        respond(503, 'Contato indisponível no momento. Ligue para nossa central.');
    }
}
$body = "Novo contato pelo site S21\n\nNome: $name\nEmpresa: $company\nE-mail: $email\nTelefone: $phone\nAssunto: $subject\n\n$message\n\nConsentimento para retorno: informado no formulário.\n";
$headers = [
    'From' => 'S21 Site <' . $config['sender'] . '>',
    'Reply-To' => $email,
    'MIME-Version' => '1.0',
    'Content-Type' => 'text/plain; charset=UTF-8',
    'Content-Transfer-Encoding' => 'base64',
];
$encodedSubject = '=?UTF-8?B?' . base64_encode('Contato S21 — ' . $subject) . '?=';
try {
    $sent = mail($config['recipient'], $encodedSubject, chunk_split(base64_encode($body)), $headers);
} catch (Throwable $exception) {
    $sent = false;
}
if (!$sent) {
    error_log('S21: servidor não aceitou o envio do formulário.');
    respond(503, 'Não foi possível enviar agora. Seus dados foram mantidos na tela. Tente novamente ou ligue para 0800 878 21 77.');
}
respond(200, 'Mensagem encaminhada! Nossa equipe retornará pelos contatos informados.');
