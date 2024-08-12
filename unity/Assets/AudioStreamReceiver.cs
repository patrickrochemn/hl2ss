using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using System.Net.Security;
using System.Security.Cryptography.X509Certificates;
using System.Net;

public class AudioStreamReceiver : MonoBehaviour
{
    private AudioSource audioSource;
    private AudioClip receivedAudioClip;

    void Start()
    {
        audioSource = gameObject.AddComponent<AudioSource>();
        ServicePointManager.ServerCertificateValidationCallback = CustomCertificateValidation;
        StartCoroutine(StreamAudio());
    }

    bool CustomCertificateValidation(object sender, X509Certificate certificate, X509Chain chain, SslPolicyErrors sslPolicyErrors)
    {
        return true; // Accept all certificates
    }

    IEnumerator StreamAudio()
    {
        string url = "http://192.168.1.23:8080";
        Debug.Log("Attempting to stream audio from: " + url);

        UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip(url, AudioType.WAV);
        yield return www.SendWebRequest();

        if (www.result == UnityWebRequest.Result.ConnectionError || www.result == UnityWebRequest.Result.ProtocolError)
        {
            Debug.LogError("Error receiving audio: " + www.error);
        }
        else if (www.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Audio stream successful.");
            receivedAudioClip = DownloadHandlerAudioClip.GetContent(www);
            PlayReceivedAudio();
        }
        else
        {
            Debug.LogWarning("Unexpected UnityWebRequest result: " + www.result);
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
