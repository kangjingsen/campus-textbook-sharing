<template>
  <div class="publish-page">
    <el-card>
      <template #header>
        <h2>📝 {{ isEdit ? '编辑教材' : '发布教材' }}</h2>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 800px;">
        <el-form-item label="书名" prop="title">
          <el-input v-model="form.title" placeholder="请输入教材名称" />
        </el-form-item>

        <el-form-item label="作者" prop="author">
          <el-input v-model="form.author" placeholder="请输入作者" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="ISBN" prop="isbn">
              <el-input v-model="form.isbn" placeholder="ISBN（可选）" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出版社" prop="publisher">
              <el-input v-model="form.publisher" placeholder="出版社（可选）" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="版次" prop="edition">
              <el-input v-model="form.edition" placeholder="如：第3版" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-cascader v-model="form.category" :options="categoryOptions"
                           :props="{ value: 'id', label: 'name', children: 'children', emitPath: false, checkStrictly: true }"
                           placeholder="选择分类" style="width: 100%;" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="新旧程度" prop="condition">
          <el-rate v-model="form.condition" :texts="['较旧', '五成新', '七成新', '九成新', '全新']" show-text />
        </el-form-item>

        <el-form-item label="交易类型" prop="transaction_type">
          <el-radio-group v-model="form.transaction_type" @change="handleTypeChange">
            <el-radio value="sell">出售</el-radio>
            <el-radio value="rent">租赁</el-radio>
            <el-radio value="free">免费赠送</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-row :gutter="16" v-if="form.transaction_type !== 'free'">
          <el-col :span="12">
            <el-form-item label="价格" prop="price">
              <el-input-number v-model="form.price" :min="0" :precision="2" :step="1" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原价（可选）">
              <el-input-number v-model="form.original_price" :min="0" :precision="2" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item v-if="form.transaction_type === 'rent'" label="租赁天数" prop="rent_duration">
          <el-input-number v-model="form.rent_duration" :min="1" :max="365" style="width: 100%;" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="描述教材的内容、状态等信息" />
        </el-form-item>

        <el-form-item label="封面图片">
          <el-upload action="#" :auto-upload="false" :limit="1" list-type="picture-card"
                     :on-change="handleFileChange" :file-list="fileList" accept="image/*">
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="handleSubmit" :loading="loading">
            {{ isEdit ? '保存修改' : '发布教材' }}
          </el-button>
          <el-button size="large" @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createTextbook, updateTextbook, getTextbookDetail, getCategoryTree } from '../api/modules'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const isEdit = computed(() => !!route.query.edit)
const categoryOptions = ref([])
const fileList = ref([])

const form = reactive({
  title: '', author: '', isbn: '', publisher: '', edition: '',
  condition: 4, description: '', price: 0, original_price: null,
  transaction_type: 'sell', rent_duration: 30, category: null,
  cover_image: null
})

const rules = {
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
  author: [{ required: true, message: '请输入作者', trigger: 'blur' }],
  transaction_type: [{ required: true, message: '请选择交易类型', trigger: 'change' }],
  condition: [{ required: true, message: '请选择新旧程度', trigger: 'change' }]
}

onMounted(async () => {
  // 加载分类
  try {
    const res = await getCategoryTree()
    categoryOptions.value = res.data.results || res.data
  } catch {}

  // 编辑模式加载原数据
  if (isEdit.value) {
    try {
      const res = await getTextbookDetail(route.query.edit)
      Object.assign(form, {
        title: res.data.title,
        author: res.data.author,
        isbn: res.data.isbn,
        publisher: res.data.publisher,
        edition: res.data.edition,
        condition: res.data.condition,
        description: res.data.description,
        price: parseFloat(res.data.price),
        original_price: res.data.original_price ? parseFloat(res.data.original_price) : null,
        transaction_type: res.data.transaction_type,
        rent_duration: res.data.rent_duration,
        category: res.data.category
      })
    } catch {}
  }
})

const handleTypeChange = (val) => {
  if (val === 'free') form.price = 0
}

const handleFileChange = (file) => {
  form.cover_image = file.raw
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    if (isEdit.value) {
      await updateTextbook(route.query.edit, form)
      ElMessage.success('修改成功')
    } else {
      await createTextbook(form)
      ElMessage.success('发布成功，等待审核')
    }
    router.push('/my-textbooks')
  } catch {} finally {
    loading.value = false
  }
}
</script>

<style scoped>
.publish-page { max-width: 900px; margin: 0 auto; }
</style>
