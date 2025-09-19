import http from 'http';

const testData = JSON.stringify({
  use_models: ['urlbert'],
  strategies: ['any', 'weighted'],
  threshold: 0.5
});

const options = {
  hostname: 'localhost',
  port: 8000,
  path: '/api/evaluate',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(testData)
  }
};

const req = http.request(options, (res) => {
  console.log(`状态码: ${res.statusCode}`);
  console.log(`响应头: ${JSON.stringify(res.headers)}`);

  res.setEncoding('utf8');
  let rawData = '';

  res.on('data', (chunk) => {
    rawData += chunk;
  });

  res.on('end', () => {
    try {
      const parsedData = JSON.parse(rawData);
      console.log('响应数据:', JSON.stringify(parsedData, null, 2));
    } catch (e) {
      console.error('解析响应失败:', e.message);
      console.log('原始响应:', rawData);
    }
  });
});

req.on('error', (e) => {
  console.error(`请求遇到问题: ${e.message}`);
});

// 写入数据到请求主体
req.write(testData);
req.end();