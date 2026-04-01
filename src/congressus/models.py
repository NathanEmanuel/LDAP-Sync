from datetime import date

from pydantic import BaseModel


class Locale(BaseModel):
    code: str
    id: int
    name: str


class Country(BaseModel):
    calling_code: str
    country_code: str
    default_locale: Locale
    id: int
    name: str
    name_local: str
    name_locale_en: str
    name_locale_nl: str


class Address(BaseModel):
    address: str | None = None
    city: str | None = None
    country: Country
    lat: float | None = None
    lng: float | None = None
    location: str | None = None
    province: str | None = None
    zip: str | None = None


class StorageFolder(BaseModel):
    id: int
    parent_id: int | None = None
    name: str
    slug: str
    path: str
    breadcrumbs: str
    published: bool


class Folder(BaseModel):
    breadcrumbs: str
    id: int
    name: str
    order_type: str
    parent_id: int
    path: str
    published: bool
    slug: str


class Phone(BaseModel):
    number: str
    number_full: str
    number_full_MSISDN: str
    number_formatted: str
    country: Country


class Logo(BaseModel):
    id: int
    url: str | None = None
    url_sm: str | None = None
    url_md: str | None = None
    url_lg: str | None = None
    is_image: bool | None = None
    type: str
    filename: str
    name: str
    size: int
    extension: str
    content_type: str
    image_width: int
    image_height: int
    folder: StorageFolder


class Group(BaseModel):
    address: Address
    description: str | None = None
    description_short: str | None = None
    email: str | None = None
    end: date | None = None
    folder: Folder
    folder_id: int
    id: int
    logo: str | None = None
    memberships: list
    memo: str
    name: str
    path: str
    phone: str | None = None
    postal_address: str | None = None
    published: bool
    slug: str
    start: date | None = None
    url: str | None = None


class GroupMembership(BaseModel):
    id: int
    member_id: int
    start: date | None = None
    end: date | None = None
    function: str | None = None
    may_edit_profile: bool
    may_manage_memberships: bool
    may_manage_storage_objects: bool
    is_self_enroll: bool
    order_type: str
    order: int
    group_id: int
    group: Group
