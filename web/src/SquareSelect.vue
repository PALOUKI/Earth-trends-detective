<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

const props = defineProps<{
  modelValue: string
  options: SelectOption[]
  placeholder: string
  accessibleLabel: string
  id: string
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const root = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const isOpen = ref(false)
const activeIndex = ref(-1)
const menuId = computed(() => `${props.id}-options`)
const selectedOption = computed(() => props.options.find((option) => option.value === props.modelValue))

function enabledIndex(start: number, direction: 1 | -1): number {
  let index = start
  while (index >= 0 && index < props.options.length) {
    if (!props.options[index].disabled) return index
    index += direction
  }
  return -1
}

function openMenu(direction: 1 | -1 = 1) {
  isOpen.value = true
  const selectedIndex = props.options.findIndex((option) => option.value === props.modelValue)
  activeIndex.value = enabledIndex(selectedIndex >= 0 ? selectedIndex : direction > 0 ? 0 : props.options.length - 1, direction)
}

function selectOption(option: SelectOption) {
  if (option.disabled) return
  emit('update:modelValue', option.value)
  isOpen.value = false
  trigger.value?.focus()
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    const direction = event.key === 'ArrowDown' ? 1 : -1
    if (!isOpen.value) openMenu(direction)
    else {
      const next = enabledIndex(activeIndex.value + direction, direction)
      if (next >= 0) activeIndex.value = next
    }
    return
  }
  if ((event.key === 'Enter' || event.key === ' ') && isOpen.value) {
    event.preventDefault()
    const option = props.options[activeIndex.value]
    if (option) selectOption(option)
    return
  }
  if (event.key === 'Escape' && isOpen.value) {
    event.preventDefault()
    isOpen.value = false
    trigger.value?.focus()
    return
  }
  if (event.key === 'Tab' && isOpen.value) {
    isOpen.value = false
    return
  }
  if (event.key === 'Home' && isOpen.value) {
    event.preventDefault()
    activeIndex.value = enabledIndex(0, 1)
  }
  if (event.key === 'End' && isOpen.value) {
    event.preventDefault()
    activeIndex.value = enabledIndex(props.options.length - 1, -1)
  }
}

function onOutsidePointer(event: PointerEvent) {
  if (root.value && !root.value.contains(event.target as Node)) isOpen.value = false
}

onMounted(() => document.addEventListener('pointerdown', onOutsidePointer))
onBeforeUnmount(() => document.removeEventListener('pointerdown', onOutsidePointer))
</script>

<template>
  <div ref="root" class="square-select" :class="{ open: isOpen }">
    <button
      :id="id"
      ref="trigger"
      class="square-select-trigger"
      type="button"
      role="combobox"
      aria-autocomplete="none"
      aria-haspopup="listbox"
      :aria-label="accessibleLabel"
      :aria-expanded="isOpen"
      :aria-controls="menuId"
      :aria-activedescendant="isOpen && activeIndex >= 0 ? `${id}-option-${activeIndex}` : undefined"
      @click="isOpen ? (isOpen = false) : openMenu()"
      @keydown="onKeydown"
    >
      <span :class="{ placeholder: !selectedOption }">{{ selectedOption?.label ?? placeholder }}</span>
      <span class="square-select-caret" aria-hidden="true">{{ isOpen ? '▴' : '▾' }}</span>
    </button>
    <div v-if="isOpen" :id="menuId" class="square-select-menu" role="listbox" :aria-label="accessibleLabel">
      <button
        v-for="(option, index) in options"
        :id="`${id}-option-${index}`"
        :key="option.value"
        class="square-select-option"
        type="button"
        tabindex="-1"
        role="option"
        :aria-selected="option.value === modelValue"
        :disabled="option.disabled"
        :class="{ active: index === activeIndex }"
        @mouseenter="activeIndex = index"
        @click="selectOption(option)"
      >{{ option.label }}</button>
    </div>
  </div>
</template>
