import { useEffect, useRef, useState } from "react";
import { ImagePlus, Trash2, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ImageUploaderProps {
  value: File | null;
  onChange: (file: File | null) => void;
  error?: string;
  disabled?: boolean;
  uploadProgress?: number;
}

export function ImageUploader({
  value,
  onChange,
  error,
  disabled = false,
  uploadProgress = 0,
}: ImageUploaderProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!value) {
      setPreviewUrl(null);
      return;
    }

    const nextUrl = URL.createObjectURL(value);
    setPreviewUrl(nextUrl);

    return () => {
      URL.revokeObjectURL(nextUrl);
    };
  }, [value]);

  const handleFileSelection = (fileList: FileList | null) => {
    const nextFile = fileList?.[0] ?? null;
    onChange(nextFile);
  };

  return (
    <div className="space-y-4">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          if (disabled) {
            return;
          }
          handleFileSelection(event.dataTransfer.files);
        }}
        className={cn(
          "rounded-3xl border border-dashed bg-muted/20 p-6 transition-colors",
          isDragging && "border-primary bg-primary/5",
          error && "border-destructive/60",
          disabled && "cursor-not-allowed opacity-70",
        )}
        aria-label="Upload waste image"
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/webp"
          className="hidden"
          disabled={disabled}
          onChange={(event) => {
            handleFileSelection(event.target.files);
            event.target.value = "";
          }}
        />

        <div className="flex flex-col items-center justify-center text-center">
          <div className="rounded-full bg-primary/10 p-4 text-primary">
            <UploadCloud className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-lg font-semibold">Drop an image here or browse</h3>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Accepted formats: JPG, JPEG, PNG, WEBP. Maximum upload size: 10 MB.
          </p>
          <Button type="button" variant="outline" className="mt-5 gap-2" disabled={disabled}>
            <ImagePlus className="h-4 w-4" />
            Choose Image
          </Button>
        </div>
      </div>

      {value && previewUrl ? (
        <div className="overflow-hidden rounded-3xl border bg-card/60 shadow-sm">
          <img
            src={previewUrl}
            alt="Selected waste preview"
            className="h-64 w-full object-cover"
          />
          <div className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-medium">{value.name}</p>
              <p className="text-sm text-muted-foreground">
                {(value.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <Button
              type="button"
              variant="ghost"
              className="gap-2 text-destructive hover:text-destructive"
              onClick={() => onChange(null)}
              disabled={disabled}
            >
              <Trash2 className="h-4 w-4" />
              Remove
            </Button>
          </div>
        </div>
      ) : null}

      {uploadProgress > 0 && uploadProgress < 100 ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Uploading image</span>
            <span className="text-muted-foreground">{uploadProgress}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted">
            <div
              className="h-2 rounded-full bg-primary transition-all"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      ) : null}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
