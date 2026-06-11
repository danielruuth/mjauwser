<template>
  <canvas 
    ref="canvasRef" 
    class="fixed inset-0 -z-50 w-full h-full pointer-events-none"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';

// Define the interface for our moving color nodes
interface MeshNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

// Default "almost white" color palette to prevent burn-in while staying bright
const defaultColors = [
  'rgba(248, 249, 250, 0.9)', // Ghost White
  'rgba(244, 244, 249, 0.9)', // Alabaster / Ice White
  'rgba(245, 245, 220, 0.6)', // Warm Beige-White (lower opacity for subtle blending)
  'rgba(250, 240, 230, 0.7)', // Linen
  'rgba(240, 248, 255, 0.8)', // Alice Blue (Cool White)
];
/*const defaultColors = [
  'rgba(255, 0, 128, 0.8)',   // Hot Pink
  'rgba(0, 255, 255, 0.8)',   // Electric Cyan
  'rgba(255, 255, 0, 0.8)',   // Neon Yellow
  'rgba(0, 255, 0, 0.8)',     // Lime Green
  'rgba(102, 0, 255, 0.8)',   // Deep Purple
];*/

const canvasRef = ref<HTMLCanvasElement | null>(null);
let animationFrameId: number;
let nodes: MeshNode[] = [];

// Initialize nodes with random positions, subtle velocities, and sizes
// Bumping speed multipliers to 4.0 so they zip across the screen
const initNodes = (width: number, height: number) => {
  nodes = defaultColors.map((color) => {
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      // Keeping it elegant but fast enough to verify visually
      vx: (Math.random() - 1.5) * 1.6,
      vy: (Math.random() - 1.5) * 1.6,
      // Shrinking to 45% of screen size so the edges are visible
      radius: Math.max(width, height) * 0.45,
      color,
    };
  });
};

const animate = (ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) => {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Base canvas background color
  ctx.fillStyle = '#fafafa';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Activate the mesh blending mode
  ctx.globalCompositeOperation = 'multiply';

  nodes.forEach((node) => {
    node.x += node.vx;
    node.y += node.vy;

    // Soft boundary bounce
    if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
    if (node.y < 0 || node.y > canvas.height) node.vy *= -1;

    // Create a radial gradient that fades completely to transparent at the edge
    const gradient = ctx.createRadialGradient(
      node.x, node.y, 0,
      node.x, node.y, node.radius
    );
    
    gradient.addColorStop(0, node.color);
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0)'); 

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    ctx.fill();
  });

  // Reset to default standard drawing mode
  ctx.globalCompositeOperation = 'source-over';

  animationFrameId = requestAnimationFrame(() => animate(ctx, canvas));
};

const handleResize = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  // Set display size based on bounds to handle high-DPI/Retina screens seamlessly
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;

  // Re-initialize nodes so they match the new aspect ratio/dimensions
  initNodes(canvas.width, canvas.height);
};

onMounted(() => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  // Set initial sizes
  handleResize();
  window.addEventListener('resize', handleResize);

  // Start the anti-burn loop
  animate(ctx, canvas);
  console.log('Gradient mesh background initialized');
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  cancelAnimationFrame(animationFrameId);
});
</script>