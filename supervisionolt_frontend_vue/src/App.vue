<template>
  <div style="padding: 20px;">
    <h1 style="color: #42b883;">Inventaire OLT</h1>

    <button @click="getDevices" style="margin-bottom: 20px; padding: 10px;">
      Charger les équipements
    </button>

    <div v-if="loading">Connexion au serveur...</div>

    <div v-if="devices.length > 0">
      <table border="1" cellpadding="10" style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="background: #f4f4f4;">
            <th>ID</th>
            <th>Nom de l'équipement</th>
            <th>Adresse IP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="device in devices" :key="device.id">
            <td>{{ device.id }}</td>
            <td>{{ device.name }}</td>
            <td>{{ device.ip_address }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-else-if="!loading && error" style="color: red;">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from './api';

const devices = ref([]);
const loading = ref(false);
const error = ref(null);

const getDevices = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.get('devices/');
    // Note : Selon ton Serializer Django, les données sont soit dans response.data,
    // soit dans response.data.results si tu as de la pagination.
    devices.value = response.data.results || response.data;
  } catch (err) {
    error.value = "Erreur Axios : " + err.message;
    console.error("Détails :", err);
  } finally {
    loading.value = false;
  }
};
</script>
