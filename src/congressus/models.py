from datetime import date as Date
from datetime import datetime as DateTime
from typing import Literal

from pydantic import BaseModel


class Locale(BaseModel):
    id: int | None = None
    name: str | None = None
    code: str | None = None


class Country(BaseModel):
    id: int | None = None
    name: str | None = None
    name_local: str | None = None
    name_locale_nl: str | None = None
    name_locale_en: str | None = None
    country_code: str | None = None
    calling_code: str | None = None
    default_locale: Locale | None = None


class Address(BaseModel):
    address: str | None = None
    zip: str | None = None
    city: str | None = None
    province: str | None = None
    country: Country | None = None
    lat: float | None = None
    lng: float | None = None
    location: str | None = None


class StorageFolder(BaseModel):
    id: int
    parent_id: int | None = None
    name: str
    slug: str
    path: str
    breadcrumbs: str
    published: bool


class Folder(BaseModel):
    id: int
    parent_id: int | None = None
    name: str
    slug: str
    path: str
    breadcrumbs: str
    published: bool
    order_type: Literal["lastname", "date", "sorted", "function"]


class FolderWithChildren(Folder):
    children: list["FolderWithChildren"]


FolderWithChildren.model_rebuild()


class PhoneNumber(BaseModel):
    number: str
    number_full: str
    number_full_MSISDN: str
    number_formatted: str
    country: Country


class StorageObject(BaseModel):
    id: int
    url: str | None = None
    url_sm: str | None = None
    url_md: str | None = None
    url_lg: str | None = None
    is_image: bool | None = None
    type: Literal["members", "files", "template", "groups", "user", "gallery", "contracts"] | None = None
    filename: str | None = None
    name: str | None = None
    size: int
    extension: str
    content_type: str
    image_width: int | None = None
    image_height: int | None = None
    folder: StorageFolder | None = None


class GroupMembership(BaseModel):
    id: int
    member_id: int
    start: Date
    end: Date | None = None
    function: str | None = None
    may_edit_profile: bool | None = None
    may_manage_memberships: bool | None = None
    may_manage_storage_objects: bool | None = None
    is_self_enroll: bool | None = None
    order_type: Literal["lastname", "date", "sorted", "function"] | None = None
    order: int | None = None
    group_id: int | None = None
    group: "Group | None" = None


class Group(BaseModel):
    id: int
    folder_id: int | None = None
    folder: Folder | None = None
    name: str
    address: Address | None = None
    postal_address: Address | None = None
    phone: PhoneNumber | None = None
    description: str | None = None
    description_short: str | None = None
    email: str | None = None
    url: str | None = None
    logo: StorageObject | None = None
    slug: str
    path: str
    published: bool
    start: Date
    end: Date | None = None
    memo: str | None = None
    memberships: list[GroupMembership] | None = None


GroupMembership.model_rebuild()


class MemberStatus(BaseModel):
    id: int
    name: str
    status_id: int
    member_from: Date
    member_to: Date | None = None
    archived: bool
    deceased: bool


class SddMandate(BaseModel):
    entity_id: int
    entity_name: str
    reference: str
    date: Date
    date_cancelled: Date | None = None
    is_valid: bool


class BankAccount(BaseModel):
    iban: str | None = None
    bic: str | None = None
    iban_formatted: str | None = None
    iban_masked: str | None = None
    sdd_mandates: list[SddMandate] | None = None


class Member(BaseModel):
    id: int
    username: str
    status: MemberStatus
    statuses: list[MemberStatus]
    gender: Literal["m", "f", "o", ""] | None = None
    prefix: str | None = None
    initials: str | None = None
    nickname: str | None = None
    given_name: str | None = None
    first_name: str | None = None
    primary_last_name_main: str | None = None
    primary_last_name_prefix: str | None = None
    primary_last_name: str
    secondary_last_name_main: str | None = None
    secondary_last_name_prefix: str | None = None
    secondary_last_name: str | None = None
    last_name_display: str | None = None
    last_name: str
    search_name: str | None = None
    suffix: str | None = None
    date_of_birth: Date | None = None
    email: str
    phone_mobile: PhoneNumber | None = None
    phone_home: PhoneNumber | None = None
    address: Address | None = None
    profile_picture_id: int | None = None
    profile_picture: StorageObject | None = None
    formal_picture_id: int | None = None
    formal_picture: StorageObject | None = None
    deleted: bool | None = None
    receive_sms: bool | None = None
    receive_mailings: bool | None = None
    locked: bool | None = None
    show_almanac: bool | None = None
    show_almanac_addresses: bool | None = None
    show_almanac_phonenumbers: bool | None = None
    show_almanac_email: bool | None = None
    show_almanac_date_of_birth: bool | None = None
    show_almanac_custom_fields: bool | None = None
    modified: DateTime | None = None
    bank_account: BankAccount | None = None
    custom_field_data: dict
