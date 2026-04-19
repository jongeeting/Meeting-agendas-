#!/usr/bin/env python3
"""
Geocoding utilities for Philadelphia addresses.

Uses the City of Philadelphia's Address Information System (AIS) API
to convert addresses to parcel numbers and coordinates.
"""

import requests
from typing import Optional, Dict
import time


class PhiladelphiaGeocoder:
    """Geocodes Philadelphia addresses using the AIS API."""

    BASE_URL = "https://api.phila.gov/ais/v1/search/"

    def __init__(self):
        """Initialize the geocoder with a simple cache."""
        self.cache: Dict[str, Optional[Dict]] = {}

    def geocode(self, address: str) -> Optional[Dict]:
        """
        Geocode a Philadelphia address to get parcel info and coordinates.

        Args:
            address: Street address in Philadelphia (e.g., "1234 Market St")

        Returns:
            Dictionary with keys: parcel_number, latitude, longitude
            Returns None if geocoding fails

        Example:
            >>> geocoder = PhiladelphiaGeocoder()
            >>> result = geocoder.geocode("131-33 S 12th St")
            >>> print(result)
            {'parcel_number': '885727860', 'latitude': 39.9497, 'longitude': -75.1601}
        """
        # Check cache first
        if address in self.cache:
            return self.cache[address]

        try:
            # Call AIS API - address goes in the URL path
            url = f"{self.BASE_URL}{address}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"Warning: AIS API returned status {response.status_code} for '{address}'")
                self.cache[address] = None
                return None

            data = response.json()

            # Extract the first feature (best match)
            if not data.get('features') or len(data['features']) == 0:
                print(f"Warning: No geocoding results for address '{address}'")
                self.cache[address] = None
                return None

            feature = data['features'][0]
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})

            # Extract parcel number (OPA account number)
            parcel_number = properties.get('opa_account_num')

            # Extract coordinates
            coordinates = geometry.get('coordinates', [])
            if len(coordinates) >= 2:
                longitude, latitude = coordinates[0], coordinates[1]
            else:
                longitude, latitude = None, None

            # Only return if we have all required fields
            if parcel_number and latitude and longitude:
                result = {
                    'parcel_number': str(parcel_number),
                    'latitude': latitude,
                    'longitude': longitude
                }
                self.cache[address] = result
                return result
            else:
                print(f"Warning: Incomplete data for address '{address}'")
                self.cache[address] = None
                return None

        except requests.exceptions.RequestException as e:
            print(f"Warning: Network error geocoding '{address}': {e}")
            self.cache[address] = None
            return None
        except Exception as e:
            print(f"Warning: Error geocoding '{address}': {e}")
            self.cache[address] = None
            return None

    def generate_buildphillynow_url(self, address: str) -> Optional[str]:
        """
        Generate a Build Philly Now parcel-page URL for an address.

        Readers following a link from the weekly digest want the FULL
        context on that property — zoning, ownership, permits, ZBA
        history, sale history — not a map popup. The parcel page
        delivers that on a dedicated URL that's also shareable.

        (Previously returned a map-with-popup URL. If you need the map
        view instead, use `/parcel/{opa}` then click "view on map" there,
        or construct the map URL manually via `result['latitude']` etc.)

        Args:
            address: Street address in Philadelphia

        Returns:
            Build Philly Now parcel-page URL, or None if geocoding fails.

        Example:
            >>> geocoder = PhiladelphiaGeocoder()
            >>> url = geocoder.generate_buildphillynow_url("131-33 S 12th St")
            >>> print(url)
            https://map.buildphillynow.org/parcel/885727860
        """
        result = self.geocode(address)

        if not result:
            return None

        parcel = result['parcel_number']
        # Strip non-digits to match BPN's /parcel/[parcelNumber] route format
        clean = "".join(c for c in str(parcel) if c.isdigit())
        if len(clean) < 5:
            return None

        return f"https://map.buildphillynow.org/parcel/{clean}"


def format_address_with_link(address: str, geocoder: Optional[PhiladelphiaGeocoder] = None) -> str:
    """
    Format an address with a Build Philly Now link if possible.

    Args:
        address: Street address
        geocoder: Optional geocoder instance (creates one if not provided)

    Returns:
        Markdown formatted string with address and link

    Example:
        >>> formatted = format_address_with_link("131-33 S 12th St")
        >>> print(formatted)
        131-33 S 12th St ([view on Build Philly Now](https://map.buildphillynow.org/?parcel=885727860&lng=-75.1601&lat=39.9497))
    """
    if not geocoder:
        geocoder = PhiladelphiaGeocoder()

    url = geocoder.generate_buildphillynow_url(address)

    if url:
        return f"{address} ([view on Build Philly Now]({url}))"
    else:
        return address


if __name__ == "__main__":
    # Test the geocoder
    geocoder = PhiladelphiaGeocoder()

    test_addresses = [
        "131-33 S 12th St",
        "1234 Market St",
        "City Hall, Philadelphia"
    ]

    for address in test_addresses:
        print(f"\nTesting: {address}")
        result = geocoder.geocode(address)
        if result:
            print(f"  Parcel: {result['parcel_number']}")
            print(f"  Lat/Lng: {result['latitude']}, {result['longitude']}")
            url = geocoder.generate_buildphillynow_url(address)
            print(f"  URL: {url}")
        else:
            print(f"  ❌ Geocoding failed")
