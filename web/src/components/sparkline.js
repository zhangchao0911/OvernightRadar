/**
 * Canvas 迷你走势图
 */

/**
 * 在指定 canvas 上绘制走势图。
 * @param {HTMLCanvasElement} canvas
 * @param {number[]} data - 价格序列
 * @param {object} options - { width, height }
 */
export function drawSparkline(canvas, data, options = {}) {
  if (!data || data.length < 2) return;

  const ctx = canvas.getContext('2d');
  const width = options.width || canvas.width || 300;
  const height = options.height || canvas.height || 80;

  canvas.width = width;
  canvas.height = height;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const padding = 2;
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;

  // 颜色：涨绿跌红（美股惯例）
  const firstVal = data[0];
  const lastVal = data[data.length - 1];
  const color = lastVal >= firstVal ? '#2e7d32' : '#c62828';

  // 绘制线条
  ctx.clearRect(0, 0, width, height);
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.lineJoin = 'round';

  for (let i = 0; i < data.length; i++) {
    const x = padding + (i / (data.length - 1)) * plotWidth;
    const y = padding + plotHeight - ((data[i] - min) / range) * plotHeight;
    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  }
  ctx.stroke();

  // 填充渐变区域
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, lastVal >= firstVal ? 'rgba(46,125,50,0.15)' : 'rgba(198,40,40,0.15)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');

  ctx.lineTo(padding + plotWidth, height);
  ctx.lineTo(padding, height);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();
}
