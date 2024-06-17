using UnityEngine;
using WebSocketSharp;
using UnityEngine.UI;
using System;
using System.Collections.Concurrent;

public class HoloLensVideoReceiver : MonoBehaviour
{
    public string serverUrl = "ws://localhost:8765";
    public RawImage rawImage;

    private WebSocket websocket;
    private Texture2D texture;
    private ConcurrentQueue<byte[]> frameQueue = new ConcurrentQueue<byte[]>();

    void Start()
    {
        texture = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
        websocket = new WebSocket(serverUrl);
        websocket.OnOpen += OnOpen;
        websocket.OnMessage += OnMessageReceived;
        websocket.OnError += OnError;
        websocket.OnClose += OnClose;
        websocket.Connect();
    }

    void Update()
    {
        if (frameQueue.TryDequeue(out byte[] imageBytes))
        {
            try
            {
                texture.LoadImage(imageBytes);
                rawImage.texture = texture;
                rawImage.SetNativeSize();
            }
            catch (Exception ex)
            {
                Debug.LogError($"Error processing frame: {ex.Message}");
            }
        }
    }

    private void OnOpen(object sender, EventArgs e)
    {
        Debug.Log("WebSocket connected!");
    }

    private void OnMessageReceived(object sender, MessageEventArgs e)
    {
        try
        {
            frameQueue.Enqueue(e.RawData);
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error enqueuing frame: {ex.Message}");
        }
    }

    private void OnError(object sender, ErrorEventArgs e)
    {
        Debug.LogError($"WebSocket error: {e.Message}");
    }

    private void OnClose(object sender, CloseEventArgs e)
    {
        Debug.Log($"WebSocket closed with reason: {e.Reason}, code: {e.Code}");
    }

    void OnDestroy()
    {
        if (websocket != null)
        {
            websocket.Close();
            websocket = null;
        }
    }
}
