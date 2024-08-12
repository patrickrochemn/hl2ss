using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System.IO;

public class AudioStreamReceiver : MonoBehaviour
{
    private AudioSource audioSource;
    private AudioClip receivedAudioClip;

    private void Start()
    {
        audioSource = gameObject.AddComponent<AudioSource>();
        StartCoroutine(StreamAudio());
    }

    IEnumerator StreamAudio()
    {
        // Adjust the URL to match audio stream source
        string url = "http://server.address/stream";

        UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip(url, AudioType.WAV);
        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.ConnectionError || www.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.Log(www.error);
        }
        else
        {
            receivedAudioClip = DownloadHandlerAudioClip.GetContent(www);
            PlayReceivedAudio();
        }
    }

    void PlayReceivedAudio()
    {
        if (receivedAudioClip != null)
        {
            audioSource.clip = receivedAudioClip;
            audioSource.Play();
        }
    }
}
