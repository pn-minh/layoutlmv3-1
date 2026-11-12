/**
 * Local HTTP/HTTPS CONNECT Forward Proxy + Persistent SSH Reverse Tunnel (-R 18888:127.0.0.1:18888)
 * Allows a firewall-restricted Vast.ai container to reach drive.usercontent.google.com,
 * script.google.com, and huggingface.co seamlessly via the local machine.
 */
const http = require('http');
const net = require('net');
const url = require('url');
const path = require('path');
const { spawn } = require('child_process');

const PROXY_PORT = 18888;
const SSH_CONFIG = path.join(__dirname, 'ssh_config');

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url);
  const options = {
    hostname: parsed.hostname,
    port: parsed.port || 80,
    path: parsed.path,
    method: req.method,
    headers: req.headers,
  };
  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });
  proxyReq.on('error', () => {
    res.writeHead(502);
    res.end('Bad Gateway');
  });
  req.pipe(proxyReq, { end: true });
});

server.on('connect', (req, clientSocket, head) => {
  const [host, portStr] = (req.url || '').split(':');
  const port = parseInt(portStr, 10) || 443;
  const serverSocket = net.connect(port, host, () => {
    clientSocket.write('HTTP/1.1 200 Connection Established\r\n\r\n');
    if (head && head.length) serverSocket.write(head);
    serverSocket.pipe(clientSocket);
    clientSocket.pipe(serverSocket);
  });
  serverSocket.on('error', () => clientSocket.destroy());
  clientSocket.on('error', () => serverSocket.destroy());
});

function startSshReverseTunnel() {
  const sshProc = spawn('ssh', [
    '-F', SSH_CONFIG,
    '-o', 'ExitOnForwardFailure=yes',
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=3',
    '-N',
    '-R', `${PROXY_PORT}:127.0.0.1:${PROXY_PORT}`,
    'vast'
  ], { stdio: 'inherit' });

  sshProc.on('exit', (code) => {
    console.log(`[SSH TUNNEL] Reverse tunnel exited (${code}), reconnecting in 3s...`);
    setTimeout(startSshReverseTunnel, 3000);
  });
}

server.listen(PROXY_PORT, '127.0.0.1', () => {
  console.log(`[PROXY] Local HTTP/HTTPS proxy listening on 127.0.0.1:${PROXY_PORT}`);
  startSshReverseTunnel();
});
