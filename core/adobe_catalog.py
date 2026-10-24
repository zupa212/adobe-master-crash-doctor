import os
from typing import Dict, Any, List, Optional

# Catalog of known Adobe Applications, executables, AppData folders, and cache directories
ADOBE_APPS_CATALOG = {
    "premiere": {
        "name": "Adobe Premiere Pro",
        "short_name": "Premiere Pro",
        "exe_names": ["Adobe Premiere Pro.exe", "premiere.exe"],
        "appdata_folder": "Premiere Pro",
        "cache_types": ["Media Cache Files", "Peak Files", "Media Cache", "Analyzer Cache Files"],
        "category": "Video Editing",
        "icon": "🎬",
        "description": "Professional timeline video editing software."
    },
    "aftereffects": {
        "name": "Adobe After Effects",
        "short_name": "After Effects",
        "exe_names": ["AfterFX.exe", "AfterEffects.exe"],
        "appdata_folder": "After Effects",
        "cache_types": ["Disk Cache", "Cache", "Peak Files"],
        "category": "Motion Graphics & VFX",
        "icon": "✨",
        "description": "Visual effects and motion graphics post-production."
    },
    "photoshop": {
        "name": "Adobe Photoshop",
        "short_name": "Photoshop",
        "exe_names": ["Photoshop.exe", "PhotoshopPrefs.exe"],
        "appdata_folder": "Adobe Photoshop*",
        "cache_types": ["CameraRaw", "AutoRecover", "FontCache", "glcache"],
        "category": "Image Editing",
        "icon": "🎨",
        "description": "Industry-standard raster graphics and digital art software."
    },
    "illustrator": {
        "name": "Adobe Illustrator",
        "short_name": "Illustrator",
        "exe_names": ["Illustrator.exe"],
        "appdata_folder": "Adobe Illustrator*",
        "cache_types": ["FontCache", "Plugin Cache", "AIRobin"],
        "category": "Vector Design",
        "icon": "📐",
        "description": "Vector graphics and illustration design platform."
    },
    "mediaencoder": {
        "name": "Adobe Media Encoder",
        "short_name": "Media Encoder",
        "exe_names": ["Adobe Media Encoder.exe", "ame.exe"],
        "appdata_folder": "Adobe Media Encoder",
        "cache_types": ["Media Cache Files", "Peak Files", "AMEQueue"],
        "category": "Video Rendering & Queue",
        "icon": "🎞️",
        "description": "Batch video and audio rendering/transcoding engine."
    },
    "audition": {
        "name": "Adobe Audition",
        "short_name": "Audition",
        "exe_names": ["Adobe Audition.exe", "audition.exe"],
        "appdata_folder": "Audition",
        "cache_types": ["Peak Files", "Audio Temp", "Conformed Files"],
        "category": "Audio Production",
        "icon": "🎙️",
        "description": "Digital audio workstation and spectral sound editor."
    },
    "lightroom": {
        "name": "Adobe Lightroom Classic",
        "short_name": "Lightroom",
        "exe_names": ["Lightroom.exe"],
        "appdata_folder": "Lightroom",
        "cache_types": ["CameraRaw", "Smart Previews", "Previews.lrdata"],
        "category": "Photography",
        "icon": "📷",
        "description": "Non-destructive RAW photo development and cataloging."
    },
    "indesign": {
        "name": "Adobe InDesign",
        "short_name": "InDesign",
        "exe_names": ["InDesign.exe"],
        "appdata_folder": "InDesign",
        "cache_types": ["InDesign SavedData", "InDesign Recovery", "FontCache"],
        "category": "Publishing & Layout",
        "icon": "📰",
        "description": "Desktop publishing, layout and typography software."
    },
    "acrobat": {
        "name": "Adobe Acrobat DC",
        "short_name": "Acrobat DC",
        "exe_names": ["Acrobat.exe", "AcroCEF.exe"],
        "appdata_folder": "Acrobat",
        "cache_types": ["AcroCEF Cache", "Security Cache"],
        "category": "PDF Document Suite",
        "icon": "📄",
        "description": "PDF editing, document workflow and form management."
    },
    "substance": {
        "name": "Adobe Substance 3D",
        "short_name": "Substance 3D",
        "exe_names": ["Adobe Substance 3D Painter.exe", "Substance 3D Painter.exe", "Adobe Substance 3D Sampler.exe", "Adobe Substance 3D Designer.exe"],
        "appdata_folder": "Adobe Substance 3D*",
        "cache_types": ["ShaderCache", "ThumbnailCache"],
        "category": "3D Texturing & Materials",
        "icon": "🧊",
        "description": "3D PBR texturing, material design and modeling suite."
    },
    "characteranimator": {
        "name": "Adobe Character Animator",
        "short_name": "Character Animator",
        "exe_names": ["Character Animator.exe"],
        "appdata_folder": "Character Animator",
        "cache_types": ["Live Puppet Cache", "Media Cache"],
        "category": "Live Animation",
        "icon": "🎭",
        "description": "Real-time webcam motion capture 2D character animation."
    }
}

def get_all_target_exe_names() -> List[str]:
    """Returns a list of all known Adobe executable filenames."""
    names = []
    for app in ADOBE_APPS_CATALOG.values():
        names.extend(app["exe_names"])
    return names

def get_app_by_id(app_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves app metadata by canonical ID."""
    return ADOBE_APPS_CATALOG.get(app_id.lower().strip())

def identify_adobe_app_by_path(exe_path: str) -> Optional[Dict[str, Any]]:
    """Identifies which Adobe app an executable belongs to."""
    if not exe_path:
        return None
    exe_name = os.path.basename(exe_path).lower().strip()
    for app_id, data in ADOBE_APPS_CATALOG.items():
        for target in data["exe_names"]:
            target_clean = target.lower().strip()
            if target_clean == exe_name or target_clean.replace(".exe", "") in exe_name:
                return {"id": app_id, "data": data}
    
    # Generic Adobe fallback
    if "adobe" in exe_path.lower():
        base = os.path.splitext(os.path.basename(exe_path))[0]
        return {
            "id": "generic_adobe",
            "data": {
                "name": base,
                "short_name": base,
                "exe_names": [os.path.basename(exe_path)],
                "appdata_folder": base,
                "cache_types": ["Cache"],
                "category": "Adobe Application",
                "icon": "⚡",
                "description": "Adobe Creative Cloud Application"
            }
        }
    return None
