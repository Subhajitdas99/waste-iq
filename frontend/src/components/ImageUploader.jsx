import { ImagePlus, Trash2, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function ImageUploader({
  value,
  onChange,
  onBlur,
  name = "image",
  error,
  disabled = false
}) {
  const cameraInputRef = useRef(null);
  const uploadInputRef = useRef(null);
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!value) {
      setPreviewUrl("");
      return undefined;
    }

    const nextPreviewUrl = URL.createObjectURL(value);
    setPreviewUrl(nextPreviewUrl);

    return () => {
      URL.revokeObjectURL(nextPreviewUrl);
    };
  }, [value]);

  function handleFileChange(event) {
    const file = event.target.files?.[0] || null;
    onChange(file);
    onBlur?.();
    event.target.value = "";
  }

  function handleRemoveImage() {
    onChange(null);
    onBlur?.();

    if (cameraInputRef.current) {
      cameraInputRef.current.value = "";
    }

    if (uploadInputRef.current) {
      uploadInputRef.current.value = "";
    }
  }

  return (
    <div className="rounded-3xl border border-ink/10 bg-white/60 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">Waste Photo</p>
          <p className="text-sm text-ink/60">Take a photo on mobile or upload an image from desktop.</p>
        </div>
        {value ? (
          <button
            type="button"
            onClick={handleRemoveImage}
            disabled={disabled}
            className="inline-flex items-center justify-center gap-2 rounded-2xl border border-coral/20 bg-coral/10 px-4 py-3 text-sm font-semibold text-coral transition hover:bg-coral/15 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Trash2 className="h-4 w-4" />
            Remove image
          </button>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => cameraInputRef.current?.click()}
          disabled={disabled}
          className="inline-flex items-center justify-center gap-2 rounded-2xl bg-leaf px-4 py-3 text-sm font-semibold text-sand transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-60"
        >
          <ImagePlus className="h-4 w-4" />
          Take Photo
        </button>
        <button
          type="button"
          onClick={() => uploadInputRef.current?.click()}
          disabled={disabled}
          className="inline-flex items-center justify-center gap-2 rounded-2xl border border-ink/10 bg-white/80 px-4 py-3 text-sm font-semibold text-ink transition hover:border-leaf hover:text-leaf disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Upload className="h-4 w-4" />
          Upload Image
        </button>
      </div>

      <input
        ref={cameraInputRef}
        name={`${name}-camera`}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="sr-only"
        disabled={disabled}
      />
      <input
        ref={uploadInputRef}
        name={`${name}-upload`}
        type="file"
        accept="image/jpeg,image/jpg,image/png,image/webp"
        onChange={handleFileChange}
        className="sr-only"
        disabled={disabled}
      />

      {previewUrl ? (
        <div className="mt-4 overflow-hidden rounded-3xl border border-white/70 bg-sand/70">
          <img src={previewUrl} alt="Selected waste preview" className="h-56 w-full object-cover" />
          <div className="px-4 py-3 text-sm text-ink/70">
            <p className="font-semibold text-ink">{value?.name}</p>
            <p>{value?.size ? `${(value.size / (1024 * 1024)).toFixed(2)} MB` : "Image selected"}</p>
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-3xl border border-dashed border-ink/10 bg-sand/60 px-4 py-8 text-center">
          <p className="text-sm font-semibold text-ink">No image selected</p>
          <p className="mt-2 text-sm text-ink/60">Accepted formats: jpg, jpeg, png, webp. Maximum size: 10 MB.</p>
        </div>
      )}

      {error ? <p className="mt-3 text-sm text-coral">{error}</p> : null}
    </div>
  );
}
