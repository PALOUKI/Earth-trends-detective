<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'

const container = ref<HTMLElement | null>(null)
let renderer: THREE.WebGLRenderer | undefined
let observer: ResizeObserver | undefined
let frame = 0
let globe: THREE.Group | undefined
let baseMaterial: THREE.MeshBasicMaterial | undefined
let temperatureMaterial: THREE.MeshBasicMaterial | undefined

onMounted(() => {
  const host = container.value
  if (!host) return

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 20)
  // Fit the whole sphere inside the square WebGL viewport with a little margin.
  camera.position.z = 5.5
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.setClearColor(0x000000, 0)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(host.clientWidth, host.clientHeight)
  renderer.outputColorSpace = THREE.SRGBColorSpace
  host.appendChild(renderer.domElement)

  const texture = new THREE.TextureLoader().load('/images/nasa-blue-marble-equirect.jpg', (loaded) => {
    loaded.colorSpace = THREE.SRGBColorSpace
  })
  const geometry = new THREE.SphereGeometry(1.38, 96, 64)
  baseMaterial = new THREE.MeshBasicMaterial({ map: texture })
  // This Blue Marble WMS texture renders its oceans almost black. Recolor
  // only the very dark water/background pixels on the home hero globe.
  baseMaterial.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <map_fragment>',
      `#include <map_fragment>
      float pixelLuma = dot(diffuseColor.rgb, vec3(0.299, 0.587, 0.114));
      float oceanMask = 1.0 - smoothstep(0.025, 0.13, pixelLuma);
      diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.0, 0.08, 0.687), oceanMask * 0.92);`,
    )
  }
  globe = new THREE.Group()
  globe.rotation.y = -0.35
  globe.rotation.z = -0.12
  globe.add(new THREE.Mesh(geometry, baseMaterial))
  scene.add(globe)

  new THREE.TextureLoader().load('/images/nasa-modis-terra-lst-day-2025-07-01.png', (temperatureTexture) => {
    if (!globe) {
      temperatureTexture.dispose()
      return
    }
    temperatureTexture.colorSpace = THREE.SRGBColorSpace
    const overlayGeometry = new THREE.SphereGeometry(1.386, 96, 64)
    temperatureMaterial = new THREE.MeshBasicMaterial({
      map: temperatureTexture,
      transparent: true,
      opacity: 0.82,
      alphaTest: 0.04,
      depthWrite: false,
    })
    globe.add(new THREE.Mesh(overlayGeometry, temperatureMaterial))
  })

  const resize = () => {
    if (!renderer || !host.clientWidth || !host.clientHeight) return
    camera.aspect = host.clientWidth / host.clientHeight
    camera.updateProjectionMatrix()
    renderer.setSize(host.clientWidth, host.clientHeight)
  }
  observer = new ResizeObserver(resize)
  observer.observe(host)

  const animate = () => {
    frame = requestAnimationFrame(animate)
    if (globe) globe.rotation.y += 0.0095
    renderer?.render(scene, camera)
  }
  animate()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  observer?.disconnect()
  globe?.traverse((object) => {
    if (object instanceof THREE.Mesh) object.geometry.dispose()
  })
  baseMaterial?.map?.dispose()
  baseMaterial?.dispose()
  temperatureMaterial?.map?.dispose()
  temperatureMaterial?.dispose()
  globe = undefined
  renderer?.dispose()
  renderer?.domElement.remove()
  renderer = undefined
})
</script>

<template>
  <div ref="container" class="hero-globe-map" role="img" aria-label="Rotating Earth with NASA Blue Marble imagery" />
</template>
