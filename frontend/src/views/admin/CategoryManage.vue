<template>
  <div class="category-manage">
    <h2>分类管理</h2>

    <el-row :gutter="16">
      <el-col :span="10">
        <el-card header="分类树">
          <el-button type="primary" size="small" @click="openAdd(null)" style="margin-bottom: 12px;">添加顶级分类</el-button>
          <el-tree :data="treeData" :props="{ label: 'name', children: 'children' }"
                   node-key="id" default-expand-all highlight-current @node-click="selectNode">
            <template #default="{ node, data }">
              <span class="tree-node">
                <span>{{ data.name }}</span>
                <span class="tree-actions">
                  <el-button link type="primary" size="small" @click.stop="openAdd(data)">添加子分类</el-button>
                  <el-button link type="primary" size="small" @click.stop="openEdit(data)">编辑</el-button>
                  <el-button link type="danger" size="small" @click.stop="deleteCategory(data)">删除</el-button>
                </span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card header="分类详情" v-if="selectedNode">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="ID">{{ selectedNode.id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
            <el-descriptions-item label="层级">{{ selectedNode.level || '-' }}</el-descriptions-item>
            <el-descriptions-item label="排序">{{ selectedNode.sort_order }}</el-descriptions-item>
            <el-descriptions-item label="子分类数">{{ selectedNode.children?.length || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-empty v-else description="点击分类查看详情" />
      </el-col>
    </el-row>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑分类' : '添加分类'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="父分类">
          <el-input :model-value="form.parent_name || '顶级分类'" disabled />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCategoryTree, createCategory, updateCategory, deleteCategory as deleteCategoryApi } from '../../api/modules'

const treeData = ref([])
const selectedNode = ref(null)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = reactive({ id: null, name: '', parent: null, parent_name: '', sort_order: 0 })

onMounted(() => loadTree())

const loadTree = async () => {
  try {
    const res = await getCategoryTree()
    treeData.value = res.data.results || res.data
  } catch {}
}

const selectNode = (data) => { selectedNode.value = data }

const openAdd = (parentNode) => {
  isEdit.value = false
  Object.assign(form, {
    id: null, name: '', sort_order: 0,
    parent: parentNode?.id || null,
    parent_name: parentNode?.name || '顶级分类'
  })
  dialogVisible.value = true
}

const openEdit = (data) => {
  isEdit.value = true
  Object.assign(form, { id: data.id, name: data.name, parent: data.parent, parent_name: '', sort_order: data.sort_order || 0 })
  dialogVisible.value = true
}

const saveCategory = async () => {
  if (!form.name.trim()) return ElMessage.warning('请输入分类名称')
  try {
    const payload = { name: form.name, parent: form.parent, sort_order: form.sort_order }
    if (isEdit.value) {
      await updateCategory(form.id, payload)
    } else {
      await createCategory(payload)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadTree()
  } catch {}
}

const deleteCategory = async (data) => {
  try {
    await ElMessageBox.confirm(`确定删除分类「${data.name}」？子分类将一并删除`, '警告', { type: 'warning' })
    await deleteCategoryApi(data.id)
    ElMessage.success('删除成功')
    if (selectedNode.value?.id === data.id) selectedNode.value = null
    loadTree()
  } catch {}
}
</script>

<style scoped>
.category-manage h2 { margin-bottom: 20px; }
.tree-node { display: flex; justify-content: space-between; align-items: center; width: 100%; padding-right: 8px; }
.tree-actions { opacity: 0; transition: opacity 0.2s; }
.tree-node:hover .tree-actions { opacity: 1; }
</style>
