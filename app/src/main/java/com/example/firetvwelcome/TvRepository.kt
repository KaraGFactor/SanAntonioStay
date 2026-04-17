package com.example.firetvwelcome

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL
import java.nio.charset.StandardCharsets

class TvRepository {
    suspend fun registerDevice(baseUrl: String, deviceId: String, deviceName: String): Result<RegisterDevicePayload> =
        withContext(Dispatchers.IO) {
            runCatching {
                require(baseUrl.isNotBlank()) { "Enter the server URL." }

                val body = JSONObject()
                    .put("deviceId", deviceId)
                    .put("deviceName", deviceName)

                val root = requestJson(
                    url = "$baseUrl/api/tv/register",
                    method = "POST",
                    body = body.toString()
                )

                RegisterDevicePayload(
                    device = parseDevice(root.getJSONObject("device")),
                    message = root.optString("message")
                )
            }
        }

    suspend fun fetchWelcome(baseUrl: String, deviceId: String): Result<WelcomePayload> =
        withContext(Dispatchers.IO) {
            runCatching {
                require(baseUrl.isNotBlank()) { "Enter the server URL." }
                require(deviceId.isNotBlank()) { "This Fire TV has not been registered yet." }

                val encodedDeviceId = URLEncoder.encode(deviceId, StandardCharsets.UTF_8)
                val root = requestJson(url = "$baseUrl/api/tv?deviceId=$encodedDeviceId")

                WelcomePayload(
                    property = parseProperty(root.getJSONObject("property")),
                    stay = parseStay(root.getJSONObject("stay")),
                    refreshSeconds = root.optInt("refreshSeconds", 300)
                )
            }
        }

    private fun requestJson(url: String, method: String = "GET", body: String? = null): JSONObject {
        val connection = (URL(url).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 10_000
            readTimeout = 10_000
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }

        try {
            if (body != null) {
                OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                    writer.write(body)
                }
            }

            val responseStream = if (connection.responseCode in 200..299) {
                connection.inputStream
            } else {
                connection.errorStream
            }

            requireNotNull(responseStream) { "The server did not return a response body." }
            val responseBody = responseStream.bufferedReader().use { it.readText() }
            val root = JSONObject(responseBody)

            if (connection.responseCode !in 200..299) {
                val message = root.optString("error").ifBlank { "Request failed." }
                error(message)
            }

            return root
        } finally {
            connection.disconnect()
        }
    }

    private fun parseDevice(root: JSONObject) = DevicePayload(
        id = root.optString("id"),
        name = root.optString("name"),
        pairingCode = root.optString("pairingCode"),
        propertyId = root.optString("propertyId"),
        status = root.optString("status")
    )

    private fun parseProperty(root: JSONObject) = PropertyPayload(
        id = root.optString("id"),
        name = root.optString("name"),
        address = root.optString("address"),
        wifiName = root.optString("wifiName"),
        wifiPassword = root.optString("wifiPassword"),
        checkInNote = root.optString("checkInNote"),
        checkoutNote = root.optString("checkoutNote"),
        houseTips = buildList {
            val tipsArray = root.optJSONArray("houseTips")
            if (tipsArray != null) {
                for (index in 0 until tipsArray.length()) {
                    add(tipsArray.optString(index))
                }
            }
        },
        contactName = root.optString("contactName"),
        contactPhone = root.optString("contactPhone")
    )

    private fun parseStay(root: JSONObject) = StayPayload(
        guestName = root.optString("guestName"),
        guestCount = root.optInt("guestCount"),
        arrivalDate = root.optString("arrivalDate"),
        departureDate = root.optString("departureDate"),
        occasion = root.optString("occasion"),
        message = root.optString("message")
    )
}
