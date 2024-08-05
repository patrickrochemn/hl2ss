using UnityEngine;
using Microsoft.MixedReality.Toolkit.UI;

public class TransformController : MonoBehaviour
{
    private Vector3 remotePosition;
    private Quaternion remoteRotation;
    private Vector3 remoteScale;

    private bool isBeingManipulated = false;

    void Start()
    {
        // Initialize with the current transform values
        remotePosition = transform.position;
        remoteRotation = transform.rotation;
        remoteScale = transform.localScale;
    }

    void Update()
    {
        if (!isBeingManipulated)
        {
            // Update the transform with remote values if not being manipulated by the user
            transform.position = remotePosition;
            transform.rotation = remoteRotation;
            transform.localScale = remoteScale;
        }
    }

    public void SetRemoteTransform(Vector3 position, Quaternion rotation, Vector3 scale)
    {
        remotePosition = position;
        remoteRotation = rotation;
        remoteScale = scale;
    }

    public Vector3 GetPosition()
    {
        return transform.position;
    }

    public Quaternion GetRotation()
    {
        return transform.rotation;
    }

    public void OnManipulationStarted(ManipulationEventData eventData)
    {
        isBeingManipulated = true;
    }

    public void OnManipulationEnded(ManipulationEventData eventData)
    {
        isBeingManipulated = false;
        // Update remote values after manipulation ends
        remotePosition = transform.position;
        remoteRotation = transform.rotation;
        remoteScale = transform.localScale;
    }
}
