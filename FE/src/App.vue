<script setup lang="ts">
import { ref } from 'vue'

interface Category {
  name: string;
  url: string;
  controls: string[];
}

const data: Category[] = [
  {
    name: 'Entra',
    url: 'https://entra.microsoft.com',
    controls: [
      "ISM-1", "ISM-2", "ISM-3", "ISM-4", "ISM-5", "ISM-6", "ISM-7", "ISM-8", "ISM-9", "ISM-10", "ISM-11", "ISM-12", "ISM-13", "ISM-14", "ISM-15", "ISM-16", "ISM-17", "ISM-18", "ISM-19", "ISM-20", "ISM-21", "ISM-22", "ISM-23", "ISM-24", "ISM-25"
    ]
  }
]

const openCategory = ref<string | null>(null)

function toggleCategory(category: string) {
  openCategory.value = openCategory.value === category ? null : category
}
</script>

<template>
  <div v-for="category in data" :key="category.name" class="mb-4">
    <div>
      <button
        class="w-full text-left px-4 py-2 bg-gray-800 text-white rounded shadow hover:bg-gray-700 focus:outline-none flex items-center justify-between"
        @click="toggleCategory(category.name)"
      >
        <div class="flex items-center">
          <span class="font-bold text-lg">{{ category.name }}</span>
          <span class="ml-2 text-sm text-blue-300">({{ category.controls.length }} controls)</span>
        </div>
        <svg
          :class="['transition-transform duration-300', openCategory === category.name ? 'rotate-90' : 'rotate-0']"
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
    <div v-if="openCategory === category.name" class="mt-2 flex flex-col gap-4">
      <div
        v-for="control in category.controls"
        :key="control"
        class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow p-4 flex flex-col items-center mx-4"
      >
        <span class="font-semibold text-gray-800 dark:text-gray-100">{{ control }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
