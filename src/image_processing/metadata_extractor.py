"""Metadata extraction module for image files

Extracts EXIF and other metadata from image files for:
- Equipment traceability
- Timestamp verification
- Camera settings documentation
- ISO/IEC 17025 compliance
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    Image = None
    TAGS = None
    GPSTAGS = None

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts metadata from image files"""

    def __init__(self):
        """Initialize metadata extractor"""
        if Image is None:
            logger.warning("PIL not available, EXIF extraction will be limited")

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from an image file

        Args:
            file_path: Path to image file

        Returns:
            Dictionary containing all extracted metadata
        """
        metadata = {}

        # File information
        metadata.update(self._get_file_info(file_path))

        # EXIF data
        if Image is not None:
            exif_data = self._extract_exif(file_path)
            if exif_data:
                metadata['exif'] = exif_data

        return metadata

    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic file information

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        stat = path.stat()

        return {
            'filename': path.name,
            'file_size_bytes': stat.st_size,
            'file_extension': path.suffix.lower(),
            'created_timestamp': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    def _extract_exif(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract EXIF metadata from image

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with EXIF data or None
        """
        if Image is None or TAGS is None:
            return None

        try:
            image = Image.open(file_path)
            exif_data = image.getexif()

            if not exif_data:
                return None

            parsed_exif = {}

            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")

                # Convert bytes to string
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='ignore')
                    except:
                        value = str(value)

                parsed_exif[tag_name] = value

            # Extract GPS data if available
            gps_info = self._extract_gps(exif_data)
            if gps_info:
                parsed_exif['GPSInfo'] = gps_info

            # Parse important fields
            parsed_exif = self._parse_exif_fields(parsed_exif)

            return parsed_exif

        except Exception as e:
            logger.warning(f"Failed to extract EXIF from {file_path}: {e}")
            return None

    def _extract_gps(self, exif_data) -> Optional[Dict[str, Any]]:
        """Extract GPS information from EXIF

        Args:
            exif_data: EXIF data from PIL

        Returns:
            Dictionary with GPS information or None
        """
        if GPSTAGS is None:
            return None

        try:
            gps_ifd = exif_data.get_ifd(0x8825)  # GPS IFD tag
            if not gps_ifd:
                return None

            gps_info = {}
            for tag_id, value in gps_ifd.items():
                tag_name = GPSTAGS.get(tag_id, f"Unknown_{tag_id}")
                gps_info[tag_name] = value

            return gps_info

        except Exception as e:
            logger.debug(f"No GPS data found: {e}")
            return None

    def _parse_exif_fields(self, exif: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and standardize important EXIF fields

        Args:
            exif: Raw EXIF dictionary

        Returns:
            Enhanced EXIF dictionary with parsed fields
        """
        # Extract camera information
        if 'Make' in exif or 'Model' in exif:
            exif['camera'] = {
                'make': exif.get('Make', 'Unknown'),
                'model': exif.get('Model', 'Unknown'),
            }

        # Extract capture settings
        settings = {}
        if 'ExposureTime' in exif:
            settings['exposure_time'] = exif['ExposureTime']
        if 'FNumber' in exif:
            settings['f_number'] = exif['FNumber']
        if 'ISOSpeedRatings' in exif:
            settings['iso'] = exif['ISOSpeedRatings']
        if 'FocalLength' in exif:
            settings['focal_length'] = exif['FocalLength']

        if settings:
            exif['capture_settings'] = settings

        # Parse datetime
        datetime_fields = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
        for field in datetime_fields:
            if field in exif:
                try:
                    dt_str = exif[field]
                    if isinstance(dt_str, str):
                        # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                        dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                        exif[f'{field}_parsed'] = dt.isoformat()
                except Exception as e:
                    logger.debug(f"Failed to parse {field}: {e}")

        # Extract image dimensions
        if 'ExifImageWidth' in exif and 'ExifImageHeight' in exif:
            exif['dimensions'] = {
                'width': exif['ExifImageWidth'],
                'height': exif['ExifImageHeight'],
            }

        return exif

    def get_equipment_info(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Extract equipment information for ISO 17025 compliance

        Args:
            metadata: Full metadata dictionary

        Returns:
            Equipment information dictionary
        """
        equipment_info = {
            'equipment_type': 'Camera',
            'manufacturer': 'Unknown',
            'model': 'Unknown',
            'serial_number': 'Unknown',
        }

        if 'exif' in metadata:
            exif = metadata['exif']

            if 'camera' in exif:
                equipment_info['manufacturer'] = exif['camera'].get('make', 'Unknown')
                equipment_info['model'] = exif['camera'].get('model', 'Unknown')

            # Try to find serial number
            if 'SerialNumber' in exif:
                equipment_info['serial_number'] = str(exif['SerialNumber'])
            elif 'BodySerialNumber' in exif:
                equipment_info['serial_number'] = str(exif['BodySerialNumber'])

        return equipment_info

    def get_capture_timestamp(self, metadata: Dict[str, Any]) -> Optional[datetime]:
        """Get the capture timestamp from metadata

        Args:
            metadata: Full metadata dictionary

        Returns:
            Capture datetime or None
        """
        if 'exif' in metadata:
            exif = metadata['exif']

            # Try parsed datetime fields first
            for field in ['DateTimeOriginal_parsed', 'DateTime_parsed']:
                if field in exif:
                    try:
                        return datetime.fromisoformat(exif[field])
                    except:
                        pass

            # Try raw datetime fields
            for field in ['DateTimeOriginal', 'DateTime']:
                if field in exif:
                    try:
                        dt_str = exif[field]
                        if isinstance(dt_str, str):
                            return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    except:
                        pass

        # Fall back to file modification time
        if 'modified_timestamp' in metadata:
            try:
                return datetime.fromisoformat(metadata['modified_timestamp'])
            except:
                pass

        return None
