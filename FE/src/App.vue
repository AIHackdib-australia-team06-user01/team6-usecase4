<script setup lang="ts">
import { ref } from 'vue'
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
</script>

<template>
  <div v-for="(controls, category) in controlsData" :key="category" class="mb-4">
    <div>
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
    </div>
    <div v-if="openCategory === category" class="mt-2 flex flex-col gap-4">
      <div
        v-for="control in controls"
        :key="control.ControlID + control.Description"
  class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow p-4 flex flex-col items-start text-left mx-4"
      >
        <span class="font-semibold text-gray-800 dark:text-gray-100">{{ control.ControlID }}</span>
        <span class="text-gray-600 dark:text-gray-300 text-sm mt-1 text-center">{{ control.Description }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
