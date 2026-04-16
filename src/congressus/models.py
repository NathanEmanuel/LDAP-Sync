from abc import ABC, abstractmethod
from datetime import date as Date
from datetime import datetime as DateTime
from typing import Literal, Optional

from pydantic import BaseModel

from common import SyncModel


class Activatable(ABC):

    @abstractmethod
    def is_active(self) -> bool: ...


class Locale(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    code: Optional[str] = None


class Country(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    name_local: Optional[str] = None
    name_locale_nl: Optional[str] = None
    name_locale_en: Optional[str] = None
    country_code: Optional[str] = None
    calling_code: Optional[str] = None
    default_locale: Optional[Locale] = None


class Address(BaseModel):
    address: Optional[str] = None
    zip: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[Country] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    location: Optional[str] = None


class StorageFolder(BaseModel):
    id: int
    parent_id: Optional[int] = None
    name: str
    slug: str
    path: str
    breadcrumbs: str
    published: bool


class Folder(BaseModel):
    id: int
    parent_id: Optional[int] = None
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
    url: Optional[str] = None
    url_sm: Optional[str] = None
    url_md: Optional[str] = None
    url_lg: Optional[str] = None
    is_image: Optional[bool] = None
    type: Optional[Literal["members", "files", "template", "groups", "user", "gallery", "contracts"]] = None
    filename: Optional[str] = None
    name: Optional[str] = None
    size: int
    extension: str
    content_type: str
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    folder: Optional[StorageFolder] = None


class GroupMembership(BaseModel, SyncModel, Activatable):
    id: int
    member_id: int
    start: Date
    end: Optional[Date] = None
    function: Optional[str] = None
    may_edit_profile: Optional[bool] = None
    may_manage_memberships: Optional[bool] = None
    may_manage_storage_objects: Optional[bool] = None
    is_self_enroll: Optional[bool] = None
    order_type: Optional[Literal["lastname", "date", "sorted", "function"]] = None
    order: Optional[int] = None
    group_id: Optional[int] = None  # not provided if object is nested under Group

    def get_id(self) -> str:
        return str(self.id)

    def is_active(self) -> bool:
        return self.end is None or self.end > Date.today()


class GroupMembershipWithGroup(GroupMembership):
    group: "Group"


class Group(BaseModel, SyncModel, Activatable):
    id: int
    folder_id: Optional[int] = None
    folder: Optional[Folder] = None
    name: str
    address: Optional[Address] = None
    postal_address: Optional[Address] = None
    phone: Optional[PhoneNumber] = None
    description: Optional[str] = None
    description_short: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    logo: Optional[StorageObject] = None
    slug: str
    path: str
    published: bool
    start: Date
    end: Optional[Date] = None
    memo: Optional[str] = None

    def get_id(self) -> str:
        return str(self.id)

    def is_active(self) -> bool:
        return self.end is None or self.end > Date.today()


class GroupWithMemberships(Group):
    memberships: list[GroupMembership]


GroupMembershipWithGroup.model_rebuild()


class MemberStatus(BaseModel, Activatable):
    id: int
    name: str
    status_id: int
    member_from: Date
    member_to: Optional[Date] = None
    archived: bool
    deceased: bool

    def is_active(self) -> bool:
        return not self.archived and not self.deceased and (self.member_to is None or self.member_to > Date.today())


class SddMandate(BaseModel, Activatable):
    entity_id: int
    entity_name: str
    reference: str
    date: Date
    date_cancelled: Optional[Date] = None
    is_valid: bool

    def is_active(self) -> bool:
        return self.is_valid and (self.date_cancelled is None or self.date_cancelled > Date.today())


class BankAccount(BaseModel):
    iban: Optional[str] = None
    bic: Optional[str] = None
    iban_formatted: Optional[str] = None
    iban_masked: Optional[str] = None
    sdd_mandates: Optional[list[SddMandate]] = None


class Member(BaseModel, SyncModel, Activatable):
    id: int
    username: str
    status: MemberStatus
    statuses: list[MemberStatus]
    gender: Optional[Literal["m", "f", "o", ""]] = None
    prefix: Optional[str] = None
    initials: Optional[str] = None
    nickname: Optional[str] = None
    given_name: Optional[str] = None
    first_name: Optional[str] = None
    primary_last_name_main: Optional[str] = None
    primary_last_name_prefix: Optional[str] = None
    primary_last_name: str
    secondary_last_name_main: Optional[str] = None
    secondary_last_name_prefix: Optional[str] = None
    secondary_last_name: Optional[str] = None
    last_name_display: Optional[str] = None
    last_name: str
    search_name: Optional[str] = None
    suffix: Optional[str] = None
    date_of_birth: Optional[Date] = None
    email: str
    phone_mobile: Optional[PhoneNumber] = None
    phone_home: Optional[PhoneNumber] = None
    address: Optional[Address] = None
    profile_picture_id: Optional[int] = None
    profile_picture: Optional[StorageObject] = None
    formal_picture_id: Optional[int] = None
    formal_picture: Optional[StorageObject] = None
    deleted: Optional[bool] = None
    receive_sms: Optional[bool] = None
    receive_mailings: Optional[bool] = None
    locked: Optional[bool] = None
    show_almanac: Optional[bool] = None
    show_almanac_addresses: Optional[bool] = None
    show_almanac_phonenumbers: Optional[bool] = None
    show_almanac_email: Optional[bool] = None
    show_almanac_date_of_birth: Optional[bool] = None
    show_almanac_custom_fields: Optional[bool] = None
    modified: Optional[DateTime] = None
    bank_account: Optional[BankAccount] = None
    custom_field_data: dict

    def get_id(self) -> str:
        return str(self.id)

    def is_active(self) -> bool:
        return not self.deleted and not self.locked and self.status.is_active()
