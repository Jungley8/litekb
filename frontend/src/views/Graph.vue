<template>
  <div class="graph-view">
    <n-card :bordered="false">
      <template #header>
        <div class="header">
          <n-icon size="24" color="#d03050"><MapOutline /></n-icon>
          <span>知识图谱可视化</span>
        </div>
      </template>

      <div class="graph-container" ref="graphContainer">
        <!-- 图谱统计 -->
        <div class="stats-bar">
          <n-tag type="info">节点: {{ stats.nodes }}</n-tag>
          <n-tag type="warning">边: {{ stats.edges }}</n-tag>
          <n-button size="small" @click="refreshGraph">刷新</n-button>
          <n-button size="small" @click="layoutGraph">重排布局</n-button>
        </div>

        <!-- D3 画布 -->
        <svg ref="svgRef" class="graph-svg"></svg>

        <!-- 图例 -->
        <div class="legend">
          <div class="legend-item">
            <span class="dot entity"></span>
            <span>实体</span>
          </div>
          <div class="legend-item">
            <span class="dot concept"></span>
            <span>概念</span>
          </div>
          <div class="legend-item">
            <span class="dot relation"></span>
            <span>关系</span>
          </div>
        </div>
      </div>

      <!-- 节点详情面板 -->
      <div v-if="selectedNode" class="node-detail">
        <n-card size="small" :bordered="false">
          <template #header>
            <div class="detail-header">
              <span>{{ selectedNode.label }}</span>
              <n-button text size="small" @click="selectedNode = null">
                <template #icon><n-icon><CloseOutline /></n-icon></template>
              </n-button>
            </div>
          </template>
          <n-descriptions :column="1" label-placement="left">
            <n-descriptions-item label="类型">
              <n-tag size="small">{{ selectedNode.type }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="描述">
              {{ selectedNode.description || '暂无描述' }}
            </n-descriptions-item>
            <n-descriptions-item label="相关文档">
              <n-space>
                <n-button
                  v-for="doc in selectedNode.documents"
                  :key="doc.id"
                  size="small"
                  text
                  type="primary"
                >
                  {{ doc.title }}
                </n-button>
              </n-space>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { MapOutline, CloseOutline } from '@vicons/ionicons5'

interface GraphNode {
  id: string
  label: string
  type: 'entity' | 'concept'
  description?: string
  documents?: Array<{ id: string; title: string }>
  x?: number
  y?: number
  fx?: number | null
  fy?: number | null
}

interface GraphLink {
  source: string | GraphNode
  target: string | GraphNode
  type: string
}

const graphContainer = ref<HTMLElement>()
const svgRef = ref<SVGSVGElement>()

const stats = ref({ nodes: 0, edges: 0 })
const selectedNode = ref<GraphNode | null>(null)

let simulation: d3.Simulation<GraphNode, undefined> | null = null

// 模拟图谱数据
const graphData = {
  nodes: [
    { id: '1', label: 'Transformer', type: 'concept' as const, description: '注意力机制架构' },
    { id: '2', label: '注意力机制', type: 'entity' as const, description: '核心机制' },
    { id: '3', label: '自注意力', type: 'entity' as const, description: '注意力的一种' },
    { id: '4', label: '多头注意力', type: 'entity' as const, description: '多个注意力头' },
    { id: '5', label: '位置编码', type: 'entity' as const, description: '位置信息注入' },
    { id: '6', label: 'BERT', type: 'concept' as const, description: '预训练模型' },
    { id: '7', label: 'GPT', type: 'concept' as const, description: '生成式预训练' },
    { id: '8', label: 'LSTM', type: 'concept' as const, description: '循环神经网络' }
  ],
  links: [
    { source: '1', target: '2', type: '包含' },
    { source: '2', target: '3', type: '演化' },
    { source: '2', target: '4', type: '包含' },
    { source: '1', target: '5', type: '使用' },
    { source: '1', target: '6', type: '应用' },
    { source: '1', target: '7', type: '应用' },
    { source: '3', target: '4', type: '包含' },
    { source: '8', target: '1', type: '演化自' }
  ]
}

function initGraph() {
  if (!svgRef.value || !graphContainer.value) return

  const width = graphContainer.value.clientWidth
  const height = graphContainer.value.clientHeight - 60

  const svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  svg.selectAll('*').remove()

  // 创建力导向图
  simulation = d3.forceSimulation<GraphNode>(graphData.nodes as GraphNode[])
    .force('link', d3.forceLink<GraphNode, GraphLink>(graphData.links)
      .id(d => d.id)
      .distance(120))
    .force('charge', d3.forceManyBody().strength(-400))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(50))

  // 绘制边
  const link = svg.append('g')
    .selectAll('line')
    .data(graphData.links)
    .join('line')
    .attr('stroke', '#999')
    .attr('stroke-width', 2)
    .attr('opacity', 0.6)

  // 绘制节点
  const node = svg.append('g')
    .selectAll('g')
    .data(graphData.nodes)
    .join('g')
    .attr('cursor', 'pointer')
    .call(d3.drag<SVGGElement, GraphNode>()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  // 节点圆形背景
  node.append('circle')
    .attr('r', 25)
    .attr('fill', d => d.type === 'concept' ? '#18a058' : '#2080f0')
    .attr('opacity', 0.2)

  // 节点图标/文字
  node.append('text')
    .text(d => d.label.substring(0, 8))
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('pointer-events', 'none')

  // 点击事件
  node.on('click', (event, d) => {
    selectedNode.value = d
    event.stopPropagation()
  })

  // 点击空白取消选择
  svg.on('click', () => {
    selectedNode.value = null
  })

  // 更新位置
  simulation.on('tick', () => {
    link
      .attr('x1', d => (d.source as GraphNode).x!)
      .attr('y1', d => (d.source as GraphNode).y!)
      .attr('x2', d => (d.target as GraphNode).x!)
      .attr('y2', d => (d.target as GraphNode).y!)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  stats.value = {
    nodes: graphData.nodes.length,
    edges: graphData.links.length
  }
}

function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, unknown>, d: GraphNode) {
  if (!event.active) simulation?.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, unknown>, d: GraphNode) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, unknown>, d: GraphNode) {
  if (!event.active) simulation?.alphaTarget(0)
  d.fx = null
  d.fy = null
}

function refreshGraph() {
  initGraph()
}

function layoutGraph() {
  simulation?.alpha(1).restart()
}

onMounted(() => {
  initGraph()
  window.addEventListener('resize', initGraph)
})

onUnmounted(() => {
  window.removeEventListener('resize', initGraph)
  simulation?.stop()
})
</script>

<style scoped>
.graph-view {
  height: calc(100vh - 112px);
}

.graph-container {
  position: relative;
  height: calc(100% - 60px);
}

.stats-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.graph-svg {
  width: 100%;
  height: 100%;
  background: #fafafa;
  border-radius: 8px;
}

.legend {
  position: absolute;
  bottom: 16px;
  right: 16px;
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.entity {
  background: #2080f0;
}

.dot.concept {
  background: #18a058;
}

.dot.relation {
  background: #999;
}

.node-detail {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 280px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
