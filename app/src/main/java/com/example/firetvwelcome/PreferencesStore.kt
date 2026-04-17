package com.example.firetvwelcome

import android.content.Context

class PreferencesStore(context: Context) {
    private val prefs = context.getSharedPreferences("firetv-welcome", Context.MODE_PRIVATE)

    fun saveServerUrl(serverUrl: String) {
        prefs.edit()
            .putString(KEY_SERVER_URL, serverUrl.trimEnd('/'))
            .apply()
    }

    fun saveDeviceId(deviceId: String) {
        prefs.edit()
            .putString(KEY_DEVICE_ID, deviceId)
            .apply()
    }

    fun hasServerUrl(): Boolean = serverUrl().isNotBlank()

    fun serverUrl(): String = prefs.getString(KEY_SERVER_URL, "") ?: ""

    fun deviceId(): String = prefs.getString(KEY_DEVICE_ID, "") ?: ""

    fun clearDeviceId() {
        prefs.edit().remove(KEY_DEVICE_ID).apply()
    }

    private companion object {
        const val KEY_SERVER_URL = "server_url"
        const val KEY_DEVICE_ID = "device_id"
    }
}
