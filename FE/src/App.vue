<script setup lang="ts">
import { ref, computed } from 'vue'
import entraData from '../public/entra_ism_ml2_technical_aligned.json'

const host = 'http://localhost:8000'

interface Control {
  ControlID: string;
  Description: string;
  Section: string;
  Topic: string;
  AlignedTopics: string;
  BlueprintArea: string;
}

interface CategoryControls {
  [category: string]: Control[];
}

const controlsData = ref<CategoryControls>(entraData);

function openOutputFile() {
  if (outputFile.value) {
    window.open(outputFile.value, '_blank');
  }
}

const openCategory = ref<string | null>(null)
function toggleCategory(category: string) {
  openCategory.value = openCategory.value === category ? null : category
}

const selectedControls = ref<Set<string>>(new Set());

function toggleControlSelection(controlID: string) {
  if (selectedControls.value.has(controlID)) {
    selectedControls.value.delete(controlID);
  } else {
    selectedControls.value.add(controlID);
  }
  // Force reactivity for Set
  selectedControls.value = new Set(selectedControls.value);
}

function deselectAll() {
  selectedControls.value = new Set();
}

// Evaluation results state
const controlsEvaluated = ref(0)
const controlsPassed = ref(0)
const controlsFailed = ref(0)
const showResults = ref(false)
const outputFile = ref('')

// Show congrats gif and text if all pass
const showCongrats = ref(false)

function evaluateControls() {
  
  // 80% chance to pass all, else fail all
  if (selectedControls.value.size === 0) {
    controlsPassed.value = 0;
    controlsFailed.value = 0;
    showCongrats.value = false;
    showResults.value = true;
    return;
  }

  const passRate = controlsPassed.value / selectedControls.value.size
  // TODO: replace this with the real evaluation logic
  if (passRate > 0.8) {
    showCongrats.value = true;
  } else {
    showCongrats.value = false;
  }
  showResults.value = true;
}

function clearResults() {
  showResults.value = false
  controlsEvaluated.value = 0
  controlsPassed.value = 0
  controlsFailed.value = 0
  showCongrats.value = false
}
// Mock service to simulate API call
const isLoading = ref(false)

async function runService() {
  isLoading.value = true
  let response = null
  try {
    response = await fetch(`${host}/conduct-assessment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        items: Array.from(selectedControls.value)
      })
    });
    // Optionally handle response here if needed
    const data = await response.json();
    // Count assessments with result 'Effective', 'Not Applicable', or 'Alternate Control'
    if (data && Array.isArray(data.assessments)) {
      controlsEvaluated.value = selectedControls.value.size
      controlsPassed.value = data.assessments.filter((a: { result: string }) => ['effective', 'not applicable', 'alternate control'].includes(a.result?.toLowerCase())).length;
      controlsFailed.value = selectedControls.value.size - controlsPassed.value;
      outputFile.value = `${host}/download-report?filename=${data.output_file}`;
    } else if (data && data.output_file) {
      outputFile.value = '';
    } else {
      controlsEvaluated.value = 0;
    }
    console.log('Service response:', data);
    console.log('Output File:', outputFile.value);
  } catch (error) {
    console.error('API error:', error);
  }

  evaluateControls()
  selectedControls.value = new Set()
  openCategory.value = null
  isLoading.value = false
}

function selectAllCategory(category: string, controls: Control[]) {
  const newSet = new Set(selectedControls.value);
  controls.forEach(ctrl => newSet.add(ctrl.ControlID));
  selectedControls.value = newSet;
}
</script>

<template>
  <div class="p-4">
    <header class="text-left mt-8 mb-6 flex flex-col items-start">
      <img src="/logo.png" alt="DISPruptor Logo" class="h-24 w-auto mb-2" style="max-width: 320px;" />
      <p class="text-base text-gray-500 dark:text-gray-300 mt-1">made by Team BluePrint</p>
    </header>
    <div v-if="showResults" class="flex flex-col items-center justify-center gap-4 mb-6">
      <div v-if="showCongrats" class="flex flex-col items-center mb-2">
        <img src="/giphy-1.gif" alt="Congratulations!" class="w-40 h-40 mb-2" />
        <span class="congrats-text text-2xl font-extrabold mb-2">🎉 Congratulations! You Passed! 🎉</span>
      </div>
      <div v-else-if="showResults && controlsFailed === controlsEvaluated && controlsEvaluated > 0" class="flex flex-col items-center mb-2">
        <img src="/giphy-2.gif" alt="Sad dog" class="w-40 h-40 mb-2" />
        <span class="fail-text text-2xl font-extrabold mb-2">😢 The dog is sad because you failed. Try again!</span>
      </div>
      <div class="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded px-4 py-2">
        <span class="font-semibold text-gray-700 dark:text-gray-200">Evaluated:</span>
        <span class="text-blue-700 dark:text-blue-400 font-bold">{{ controlsEvaluated }}</span>
        <span class="ml-4 font-semibold text-green-700 dark:text-green-400">Passed:</span>
        <span class="text-green-700 dark:text-green-400 font-bold">{{ controlsPassed }}</span>
        <span class="ml-4 font-semibold text-red-700 dark:text-red-400">Failed:</span>
        <span class="text-red-700 dark:text-red-400 font-bold">{{ controlsFailed }}</span>
      </div>
      <button
        v-if="outputFile && outputFile !== ''"
        @click="openOutputFile"
        class="px-3 py-1.5 bg-green-600 text-white rounded shadow hover:bg-green-700 focus:outline-none transition mb-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 mr-1 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5 5-5M12 15V3" />
        </svg>
        Download Results
      </button>
      <button @click="clearResults" class="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded shadow hover:bg-gray-300 dark:hover:bg-gray-600 focus:outline-none transition">Clear Results</button>
    </div>



    <div v-if="isLoading" class="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black bg-opacity-80">
      <img src="/giphy.gif" alt="Loading..." class="w-40 h-40 mb-6" />
      <span class="text-white text-2xl font-bold animate-pulse">Loading...</span>
    </div>
    <!-- <div class="max-w-xl mx-auto mt-6" :class="{ 'pointer-events-none opacity-40': isLoading }"> -->
    <div class="flex items-center mb-4 gap-4 flex-wrap justify-between">
      <div class="flex items-center gap-3 flex-wrap">
        <div v-if="selectedControls.size" class="bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded px-3 py-2 min-w-[120px] flex flex-col items-start">
          <span class="text-xs font-semibold text-gray-500 mb-1 block">Selected Controls:</span>
          <ul class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-1 text-xs text-gray-800 dark:text-gray-100">
            <li v-for="ctrl in Array.from(selectedControls).sort()" :key="ctrl" class="truncate px-1 py-0.5 bg-white dark:bg-gray-900 rounded shadow-sm border border-gray-200 dark:border-gray-700 text-center">
              {{ ctrl }}
            </li>
          </ul>
          <button
            @click="deselectAll()"
            class="mt-2 px-2 py-0.5 text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded hover:bg-red-200 dark:hover:bg-red-800 transition"
          >
            Deselect All
          </button>
        </div>
        <span v-if="isLoading" class="text-blue-600 text-sm ml-2">Service is running...</span>
      </div>
      <button
        @click="runService"
        :disabled="isLoading || selectedControls.size === 0"
        class="flex items-center px-3 py-1.5 bg-blue-600 text-white rounded shadow hover:bg-blue-700 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed ml-auto"
      >
        <svg v-if="!isLoading" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5 mr-1">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v18l15-9-15-9z" />
        </svg>
        <svg v-else class="animate-spin w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
        </svg>
        <span>{{ isLoading ? 'Loading...' : 'Evaluate' }}</span>
      </button>
    </div>
    <div v-for="(controls, category) in controlsData" :key="category" class="mb-4">
      <div class="flex items-center gap-2 mb-1">
        <button
          class="flex-1 text-left px-4 py-2 bg-gray-800 text-white rounded shadow hover:bg-gray-700 focus:outline-none flex items-center justify-between"
          @click="toggleCategory(String(category))"
        >
          <div class="flex items-center">
            <span class="font-bold text-lg">{{ category }}</span>
            <span class="ml-2 text-sm text-blue-300">({{ controls.filter((ctrl, idx, arr) => arr.findIndex(c => c.ControlID === ctrl.ControlID) === idx).length }} controls)</span>
            <button
          class="px-2 py-1 mx-2 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded shadow hover:bg-blue-200 dark:hover:bg-blue-800 text-xs font-semibold"
          @click.stop="selectAllCategory(String(category), controls)"
        >
          Select All
        </button>
          </div>
          <svg
            :class="['transition-transform duration-300', openCategory === category ? 'rotate-90' : 'rotate-0']"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            class="w-5 h-5 ml-2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
       
      </div>

      <ul v-if="openCategory === category" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700 mt-2">
        <li
          v-for="control in controls.filter((ctrl, idx, arr) => arr.findIndex(c => c.ControlID === ctrl.ControlID) === idx).sort((a, b) => a.ControlID.localeCompare(b.ControlID))"
          :key="control.ControlID"
          class="flex items-center px-2 py-1 transition-all duration-200 ease-in-out relative group hover:bg-gray-100 dark:hover:bg-gray-800 hover:py-3"
        >
          <label
            :for="category + '-' + control.ControlID"
            class="font-semibold text-gray-800 dark:text-gray-100 cursor-pointer flex flex-row items-center gap-3 text-sm py-2 px-2 rounded hover:bg-blue-50 dark:hover:bg-blue-900 transition-all w-full"
            style="user-select: none;"
          >
            <input
              type="checkbox"
              class="form-checkbox h-5 w-5 text-blue-600 mr-2 cursor-pointer"
              :id="category + '-' + control.ControlID"
              :checked="selectedControls.has(control.ControlID)"
              @change="toggleControlSelection(control.ControlID)"
              tabindex="0"
            />
            <div class="flex flex-col">
              <span>{{ control.ControlID }}</span>
              <span
                class="text-gray-600 dark:text-gray-300 text-xs mt-0.5 max-w-xl transition-all duration-200 opacity-0 max-h-0 group-hover:opacity-100 group-hover:max-h-32 overflow-hidden"
              >
                {{ control.Description }}
              </span>
            </div>
          </label>
        </li>
      </ul>
    </div>
  </div>
</template>
   <style scoped>
.congrats-text {
  animation: colorchange 2s infinite;
}
@keyframes colorchange {
  0%   { color: #e74c3c; }
  25%  { color: #f1c40f; }
  50%  { color: #2ecc71; }
  75%  { color: #3498db; }
  100% { color: #e74c3c; }
}
</style>
.fail-text {
  animation: colorchange 2s infinite;
}