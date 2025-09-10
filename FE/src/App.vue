<script setup lang="ts">
import { ref, computed } from 'vue'
import entraData from '../public/entra_ism_ml2_technical_aligned.json'

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

// Mock service to simulate API call
const isLoading = ref(false)
async function runService() {
  isLoading.value = true
  await new Promise(resolve => setTimeout(resolve, 4444)) // Simulate 2s delay
  isLoading.value = false
}
</script>

<template>
  <div class="p-4">
    <header class="text-left mt-8 mb-6">
      <h1 class="text-3xl font-extrabold text-blue-700 dark:text-blue-400 tracking-tight">DISPruptor</h1>
      <p class="text-base text-gray-500 dark:text-gray-300 mt-1">made by Team BluePrint</p>
    </header>
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
            @click="selectedControls.clear(); selectedControls.value = new Set()"
            class="mt-2 px-2 py-0.5 text-xs bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded hover:bg-red-200 dark:hover:bg-red-800 transition"
          >
            Deselect All
          </button>
        </div>
        <span v-if="isLoading" class="text-blue-600 text-sm ml-2">Service is running...</span>
      </div>
      <button
        @click="runService"
        :disabled="isLoading"
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
      <button
        class="w-full text-left px-4 py-2 bg-gray-800 text-white rounded shadow hover:bg-gray-700 focus:outline-none flex items-center justify-between"
        @click="toggleCategory(category)"
      >
        <div class="flex items-center">
          <span class="font-bold text-lg">{{ category }}</span>
          <span class="ml-2 text-sm text-blue-300">({{ controls.length }} controls)</span>
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
      <ul v-if="openCategory === category" class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow divide-y divide-gray-200 dark:divide-gray-700 mt-2">
        <li
          v-for="control in controls.filter((ctrl, idx, arr) => arr.findIndex(c => c.ControlID === ctrl.ControlID) === idx).sort((a, b) => a.ControlID.localeCompare(b.ControlID))"
          :key="control.ControlID"
          class="flex items-center px-2 py-1 transition-all duration-200 ease-in-out relative group hover:bg-gray-100 dark:hover:bg-gray-800 hover:py-3"
        >
          <input
            type="checkbox"
            class="form-checkbox h-4 w-4 text-blue-600 mr-2"
            :id="category + '-' + control.ControlID"
            :checked="selectedControls.has(control.ControlID)"
            @change="toggleControlSelection(control.ControlID)"
          />
          <label :for="category + '-' + control.ControlID" class="font-semibold text-gray-800 dark:text-gray-100 cursor-pointer flex flex-col text-sm">
            <span>{{ control.ControlID }}</span>
            <span
              class="text-gray-600 dark:text-gray-300 text-xs mt-0.5 max-w-xl transition-all duration-200 opacity-0 max-h-0 group-hover:opacity-100 group-hover:max-h-32 overflow-hidden"
            >
              {{ control.Description }}
            </span>
          </label>
        </li>
      </ul>
    </div>
  </div>
</template>
   