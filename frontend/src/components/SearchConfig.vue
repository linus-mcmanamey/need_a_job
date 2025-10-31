<script setup>
import { ref, onMounted } from 'vue'
import { Icon } from '@iconify/vue'
import { useSearchConfigStore } from '../stores/searchConfigStore'

const searchStore = useSearchConfigStore()

// Form state
const config = ref({
  job_type: 'contract',
  duration: '3-12+ months',
  locations: {
    primary: 'Remote (Australia-wide)',
    acceptable: 'Hybrid with >70% remote',
    exclude: ['Full office-based']
  },
  keywords: {
    primary: ['Data Engineer', 'Senior Data Engineer', 'Data Engineering'],
    secondary: ['Analytics Engineer', 'Data Platform Engineer'],
    exclude: ['Junior', 'Graduate']
  },
  technologies: {
    must_have: ['Python', 'SQL', 'Cloud Platform (Azure/AWS/GCP)'],
    strong_preference: ['PySpark', 'Azure Synapse', 'Databricks', 'Azure Data Factory', 'dbt'],
    nice_to_have: ['Airflow', 'Kafka', 'Docker/Kubernetes', 'CI/CD']
  },
  salary_expectations: {
    minimum: 800,
    target: 1000,
    maximum: 1500
  },
  seek: {
    enabled: true,
    search_terms: ['data engineer', 'data engineering'],
    location: 'Australia',
    exclude_keywords: []
  },
  indeed: {
    enabled: true,
    search_terms: ['data engineer', 'data engineering'],
    location: 'Australia',
    exclude_keywords: []
  }
})

// Temp input states for adding items
const newPrimaryKeyword = ref('')
const newSecondaryKeyword = ref('')
const newExcludeKeyword = ref('')
const newMustHaveTech = ref('')
const newStrongPrefTech = ref('')
const newNiceToHaveTech = ref('')
const newLocationExclude = ref('')
const newSeekTerm = ref('')
const newIndeedTerm = ref('')

// Loading and save states
const loading = ref(false)
const saving = ref(false)
const saveSuccess = ref(false)
const saveError = ref(null)

// Load configuration on mount
onMounted(async () => {
  loading.value = true
  try {
    const data = await searchStore.loadConfig()
    if (data) {
      config.value = data
    }
  } catch (error) {
    console.error('Failed to load config:', error)
  } finally {
    loading.value = false
  }
})

// Add/remove array items
const addItem = (array, value, inputRef) => {
  if (value.trim() && !array.includes(value.trim())) {
    array.push(value.trim())
    inputRef.value = ''
  }
}

const removeItem = (array, index) => {
  array.splice(index, 1)
}

// Save configuration
const saveConfig = async () => {
  saving.value = true
  saveSuccess.value = false
  saveError.value = null

  try {
    await searchStore.saveConfig(config.value)
    saveSuccess.value = true
    setTimeout(() => {
      saveSuccess.value = false
    }, 3000)
  } catch (error) {
    console.error('Failed to save config:', error)
    saveError.value = error.message || 'Failed to save configuration'
    setTimeout(() => {
      saveError.value = null
    }, 5000)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <h2 class="text-3xl font-bold text-slate-50 mb-2">Search Configuration</h2>
      <p class="text-slate-400">Configure job search parameters and matching criteria</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
    </div>

    <!-- Configuration Form -->
    <div v-else class="space-y-6">
      <!-- Save Success Banner -->
      <div
        v-if="saveSuccess"
        class="bg-success-900/20 border-l-4 border-success-500 rounded-xl p-5 shadow-lg animate-slide-up backdrop-blur-sm border border-success-800"
      >
        <div class="flex items-center">
          <Icon icon="heroicons:check-circle" class="w-6 h-6 text-success-400 mr-3" />
          <p class="text-success-300 font-bold">Configuration saved successfully!</p>
        </div>
      </div>

      <!-- Save Error Banner -->
      <div
        v-if="saveError"
        class="bg-danger-900/20 border-l-4 border-danger-500 rounded-xl p-5 shadow-lg animate-slide-up backdrop-blur-sm border border-danger-800"
      >
        <div class="flex items-start">
          <Icon icon="heroicons:exclamation-triangle" class="w-6 h-6 text-danger-400 mr-3" />
          <div class="flex-1">
            <p class="text-danger-300 font-bold">Failed to save configuration</p>
            <p class="text-danger-400 text-sm mt-1">{{ saveError }}</p>
          </div>
        </div>
      </div>

      <!-- Job Preferences Section -->
      <div class="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-50 mb-4 flex items-center">
          <Icon icon="heroicons:briefcase" class="w-6 h-6 mr-3" />
          Job Preferences
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Job Type -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Job Type</label>
            <select
              v-model="config.job_type"
              class="w-full px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 focus:outline-none focus:border-primary-500 transition-colors"
            >
              <option value="contract">Contract</option>
              <option value="permanent">Permanent</option>
              <option value="casual">Casual</option>
            </select>
          </div>

          <!-- Duration -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Duration</label>
            <input
              v-model="config.duration"
              type="text"
              class="w-full px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
              placeholder="e.g., 3-12+ months"
            />
          </div>
        </div>
      </div>

      <!-- Location Preferences Section -->
      <div class="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-50 mb-4 flex items-center">
          <Icon icon="heroicons:map-pin" class="w-6 h-6 mr-3" />
          Location Preferences
        </h3>

        <div class="space-y-4">
          <!-- Primary Location -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Primary Location</label>
            <input
              v-model="config.locations.primary"
              type="text"
              class="w-full px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
              placeholder="e.g., Remote (Australia-wide)"
            />
          </div>

          <!-- Acceptable Location -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Acceptable Alternative</label>
            <input
              v-model="config.locations.acceptable"
              type="text"
              class="w-full px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
              placeholder="e.g., Hybrid with >70% remote"
            />
          </div>

          <!-- Exclude Locations -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Exclude Locations</label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newLocationExclude"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add location to exclude..."
                @keyup.enter="addItem(config.locations.exclude, newLocationExclude, { value: newLocationExclude }); newLocationExclude = ''"
              />
              <button
                @click="addItem(config.locations.exclude, newLocationExclude, { value: newLocationExclude }); newLocationExclude = ''"
                class="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(location, index) in config.locations.exclude"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-slate-800 text-slate-300 rounded-lg text-sm"
              >
                {{ location }}
                <button
                  @click="removeItem(config.locations.exclude, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Keywords Section -->
      <div class="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-50 mb-4 flex items-center">
          <Icon icon="heroicons:key" class="w-6 h-6 mr-3" />
          Job Title Keywords
        </h3>

        <div class="space-y-6">
          <!-- Primary Keywords -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">
              Primary Keywords
              <span class="text-slate-500 font-normal ml-2">(Highest priority)</span>
            </label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newPrimaryKeyword"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add primary keyword..."
                @keyup.enter="addItem(config.keywords.primary, newPrimaryKeyword, { value: newPrimaryKeyword }); newPrimaryKeyword = ''"
              />
              <button
                @click="addItem(config.keywords.primary, newPrimaryKeyword, { value: newPrimaryKeyword }); newPrimaryKeyword = ''"
                class="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(keyword, index) in config.keywords.primary"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-primary-900/30 text-primary-300 rounded-lg text-sm border border-primary-800"
              >
                {{ keyword }}
                <button
                  @click="removeItem(config.keywords.primary, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>

          <!-- Secondary Keywords -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">
              Secondary Keywords
              <span class="text-slate-500 font-normal ml-2">(Acceptable alternatives)</span>
            </label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newSecondaryKeyword"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add secondary keyword..."
                @keyup.enter="addItem(config.keywords.secondary, newSecondaryKeyword, { value: newSecondaryKeyword }); newSecondaryKeyword = ''"
              />
              <button
                @click="addItem(config.keywords.secondary, newSecondaryKeyword, { value: newSecondaryKeyword }); newSecondaryKeyword = ''"
                class="px-6 py-3 bg-accent-600 hover:bg-accent-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(keyword, index) in config.keywords.secondary"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-accent-900/30 text-accent-300 rounded-lg text-sm border border-accent-800"
              >
                {{ keyword }}
                <button
                  @click="removeItem(config.keywords.secondary, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>

          <!-- Exclude Keywords -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">
              Exclude Keywords
              <span class="text-slate-500 font-normal ml-2">(Automatically reject)</span>
            </label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newExcludeKeyword"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add keyword to exclude..."
                @keyup.enter="addItem(config.keywords.exclude, newExcludeKeyword, { value: newExcludeKeyword }); newExcludeKeyword = ''"
              />
              <button
                @click="addItem(config.keywords.exclude, newExcludeKeyword, { value: newExcludeKeyword }); newExcludeKeyword = ''"
                class="px-6 py-3 bg-danger-600 hover:bg-danger-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(keyword, index) in config.keywords.exclude"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-danger-900/30 text-danger-300 rounded-lg text-sm border border-danger-800"
              >
                {{ keyword }}
                <button
                  @click="removeItem(config.keywords.exclude, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Technologies Section -->
      <div class="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-50 mb-4 flex items-center">
          <Icon icon="heroicons:wrench-screwdriver" class="w-6 h-6 mr-3" />
          Technology & Skills
        </h3>

        <div class="space-y-6">
          <!-- Must Have -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">
              Must Have
              <span class="text-slate-500 font-normal ml-2">(Required for matching)</span>
            </label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newMustHaveTech"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add required technology..."
                @keyup.enter="addItem(config.technologies.must_have, newMustHaveTech, { value: newMustHaveTech }); newMustHaveTech = ''"
              />
              <button
                @click="addItem(config.technologies.must_have, newMustHaveTech, { value: newMustHaveTech }); newMustHaveTech = ''"
                class="px-6 py-3 bg-success-600 hover:bg-success-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(tech, index) in config.technologies.must_have"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-success-900/30 text-success-300 rounded-lg text-sm border border-success-800"
              >
                {{ tech }}
                <button
                  @click="removeItem(config.technologies.must_have, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>

          <!-- Strong Preference -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">
              Strong Preference
              <span class="text-slate-500 font-normal ml-2">(Increases match score)</span>
            </label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newStrongPrefTech"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add preferred technology..."
                @keyup.enter="addItem(config.technologies.strong_preference, newStrongPrefTech, { value: newStrongPrefTech }); newStrongPrefTech = ''"
              />
              <button
                @click="addItem(config.technologies.strong_preference, newStrongPrefTech, { value: newStrongPrefTech }); newStrongPrefTech = ''"
                class="px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(tech, index) in config.technologies.strong_preference"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-primary-900/30 text-primary-300 rounded-lg text-sm border border-primary-800"
              >
                {{ tech }}
                <button
                  @click="removeItem(config.technologies.strong_preference, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>

          <!-- Nice to Have -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">
              Nice to Have
              <span class="text-slate-500 font-normal ml-2">(Minor bonus)</span>
            </label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="newNiceToHaveTech"
                type="text"
                class="flex-1 px-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                placeholder="Add nice-to-have technology..."
                @keyup.enter="addItem(config.technologies.nice_to_have, newNiceToHaveTech, { value: newNiceToHaveTech }); newNiceToHaveTech = ''"
              />
              <button
                @click="addItem(config.technologies.nice_to_have, newNiceToHaveTech, { value: newNiceToHaveTech }); newNiceToHaveTech = ''"
                class="px-6 py-3 bg-accent-600 hover:bg-accent-700 text-white font-semibold rounded-xl transition-colors"
              >
                Add
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="(tech, index) in config.technologies.nice_to_have"
                :key="index"
                class="inline-flex items-center gap-2 px-3 py-1 bg-accent-900/30 text-accent-300 rounded-lg text-sm border border-accent-800"
              >
                {{ tech }}
                <button
                  @click="removeItem(config.technologies.nice_to_have, index)"
                  class="text-danger-400 hover:text-danger-300 transition-colors"
                >
                  ×
                </button>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Salary Expectations Section -->
      <div class="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-50 mb-4 flex items-center">
          <Icon icon="heroicons:currency-dollar" class="w-6 h-6 mr-3" />
          Salary Expectations (AUD per day)
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <!-- Minimum -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Minimum</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400">$</span>
              <input
                v-model.number="config.salary_expectations.minimum"
                type="number"
                class="w-full pl-10 pr-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 focus:outline-none focus:border-danger-500 transition-colors"
              />
            </div>
          </div>

          <!-- Target -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Target</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400">$</span>
              <input
                v-model.number="config.salary_expectations.target"
                type="number"
                class="w-full pl-10 pr-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 focus:outline-none focus:border-primary-500 transition-colors"
              />
            </div>
          </div>

          <!-- Maximum -->
          <div>
            <label class="block text-sm font-semibold text-slate-300 mb-2">Maximum</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400">$</span>
              <input
                v-model.number="config.salary_expectations.maximum"
                type="number"
                class="w-full pl-10 pr-4 py-3 bg-slate-800 border-2 border-slate-700 rounded-xl text-slate-100 focus:outline-none focus:border-success-500 transition-colors"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Job Boards Section -->
      <div class="bg-slate-900 rounded-2xl shadow-lg border border-slate-800 p-6">
        <h3 class="text-xl font-bold text-slate-50 mb-4 flex items-center">
          <Icon icon="heroicons:globe-alt" class="w-6 h-6 mr-3" />
          Job Boards
        </h3>

        <div class="space-y-6">
          <!-- SEEK -->
          <div class="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
            <div class="flex items-center justify-between mb-4">
              <h4 class="text-lg font-bold text-slate-50">SEEK</h4>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  v-model="config.seek.enabled"
                  type="checkbox"
                  class="sr-only peer"
                />
                <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>

            <div class="space-y-3">
              <div>
                <label class="block text-sm font-semibold text-slate-300 mb-2">Location</label>
                <input
                  v-model="config.seek.location"
                  type="text"
                  class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                  placeholder="e.g., Australia"
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-300 mb-2">Search Terms</label>
                <div class="flex gap-2 mb-2">
                  <input
                    v-model="newSeekTerm"
                    type="text"
                    class="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                    placeholder="Add search term..."
                    @keyup.enter="addItem(config.seek.search_terms, newSeekTerm, { value: newSeekTerm }); newSeekTerm = ''"
                  />
                  <button
                    @click="addItem(config.seek.search_terms, newSeekTerm, { value: newSeekTerm }); newSeekTerm = ''"
                    class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="(term, index) in config.seek.search_terms"
                    :key="index"
                    class="inline-flex items-center gap-2 px-3 py-1 bg-slate-700 text-slate-300 rounded-lg text-sm"
                  >
                    {{ term }}
                    <button
                      @click="removeItem(config.seek.search_terms, index)"
                      class="text-danger-400 hover:text-danger-300 transition-colors"
                    >
                      ×
                    </button>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Indeed -->
          <div class="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
            <div class="flex items-center justify-between mb-4">
              <h4 class="text-lg font-bold text-slate-50">Indeed</h4>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  v-model="config.indeed.enabled"
                  type="checkbox"
                  class="sr-only peer"
                />
                <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
              </label>
            </div>

            <div class="space-y-3">
              <div>
                <label class="block text-sm font-semibold text-slate-300 mb-2">Location</label>
                <input
                  v-model="config.indeed.location"
                  type="text"
                  class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                  placeholder="e.g., Australia"
                />
              </div>

              <div>
                <label class="block text-sm font-semibold text-slate-300 mb-2">Search Terms</label>
                <div class="flex gap-2 mb-2">
                  <input
                    v-model="newIndeedTerm"
                    type="text"
                    class="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-400 focus:outline-none focus:border-primary-500 transition-colors"
                    placeholder="Add search term..."
                    @keyup.enter="addItem(config.indeed.search_terms, newIndeedTerm, { value: newIndeedTerm }); newIndeedTerm = ''"
                  />
                  <button
                    @click="addItem(config.indeed.search_terms, newIndeedTerm, { value: newIndeedTerm }); newIndeedTerm = ''"
                    class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="(term, index) in config.indeed.search_terms"
                    :key="index"
                    class="inline-flex items-center gap-2 px-3 py-1 bg-slate-700 text-slate-300 rounded-lg text-sm"
                  >
                    {{ term }}
                    <button
                      @click="removeItem(config.indeed.search_terms, index)"
                      class="text-danger-400 hover:text-danger-300 transition-colors"
                    >
                      ×
                    </button>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Save Button -->
      <div class="flex justify-end sticky bottom-6">
        <button
          @click="saveConfig"
          :disabled="saving"
          class="px-8 py-4 bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 text-white font-bold text-lg rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="saving" class="flex items-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Saving...
          </span>
          <span v-else class="flex items-center gap-2">
            <Icon icon="heroicons:check-circle" class="w-5 h-5" />
            Save Configuration
          </span>
        </button>
      </div>
    </div>
  </div>
</template>
