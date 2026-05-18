#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Album, Article, Category, Photo  # noqa: E402


VOYAGE_MEDIA_SPECS: list[dict[str, Any]] = [
    {
        "title_fr": "Provence, France",
        "title_cn": "普罗旺斯：薰衣草之乡",
        "desc_fr": "Lavender fields, limestone villages, and warm Mediterranean light.",
        "desc_cn": "薰衣草田、石灰岩村庄与地中海暖光交织成夏日风景。",
        "prefixes": ["provans-", "provence-"],
        "captions_fr": [
            "La lumiere glisse sur les collines en silence.",
            "Un village de pierre respire a l'heure lente.",
            "Les routes blanches traversent la chaleur des herbes.",
            "Au loin, la lavande trace une mer immobile.",
            "Le vent porte l'odeur du thym et de la poussiere dorée.",
            "Les volets pales ferment la sieste du midi.",
            "Les cyprès gardent la ligne du ciel.",
            "Le soir se pose sur les murs couleur de miel.",
        ],
        "captions_cn": [
            "光在丘陵上缓缓流动，像一段安静的独白。",
            "石头小镇在慢时光里呼吸。",
            "白色公路穿过草木灼热的气息。",
            "远处的薰衣草像一片静止的海。",
            "风里有百里香与金色尘土的味道。",
            "浅色木窗合上了正午的午憩。",
            "柏树守着天空的轮廓线。",
            "傍晚落在蜂蜜色的墙面上。",
        ],
    },
    {
        "title_fr": "Bordighera, Italie",
        "title_cn": "博尔迪盖拉：意式边境",
        "desc_fr": "Palm-lined promenades and the soft frontier breeze between sea and hills.",
        "desc_cn": "棕榈步道与海风在丘陵与海岸之间交汇，边境气息温柔而鲜明。",
        "prefixes": ["bordighera-"],
        "captions_fr": [
            "Les palmiers inclinent leur ombre vers la mer.",
            "L'apres-midi dore les facades du front de mer.",
            "Dans les ruelles, la pierre garde la fraicheur.",
            "Le rivage parle bas entre Italie et azur.",
            "Une terrasse vide attend le cafe du soir.",
            "Les voiles blanches coupent la ligne de l'horizon.",
            "La lumiere saline polit les vieux escaliers.",
            "Le crepuscule fait vibrer les toits ocre.",
            "Un parfum d'agrumes descend des jardins.",
            "La nuit allume des perles sur la baie.",
        ],
        "captions_cn": [
            "棕榈的影子向海面轻轻倾斜。",
            "午后把海滨立面镀成温暖的金色。",
            "巷道里的石墙仍留着阴凉。",
            "海岸在意大利与蔚蓝之间低声交谈。",
            "空露台等待傍晚的一杯咖啡。",
            "白帆切开平直的地平线。",
            "带盐分的光把旧阶梯磨得发亮。",
            "暮色让赭色屋顶微微震颤。",
            "柑橘香从花园深处缓缓落下。",
            "夜色在海湾点起珍珠般的灯。",
        ],
    },
    {
        "title_fr": "Cinque Terre, Italie",
        "title_cn": "五渔村：悬崖上的斑斓",
        "desc_fr": "Colorful cliff villages, terraces, and a restless blue sea.",
        "desc_cn": "彩色村落悬于峭壁，梯田与海浪共同构成五渔村的节奏。",
        "prefixes": ["cinqueterre-"],
        "captions_fr": [
            "Les maisons couleur corail tiennent au bord du vide.",
            "Le sentier monte entre vigne et falaise.",
            "La mer frappe, puis retire son souffle.",
            "Un balcon regarde les barques rentrer tard.",
            "Les rails suivent la courbe des rochers.",
            "Le village se plie a la pente avec grace.",
            "Le bleu profond avale les dernieres voix du jour.",
            "Les filets sechent comme des drapeaux de sel.",
            "Le soleil descend derriere les terrasses en etages.",
            "Le soir met du cuivre sur les toits et les vagues.",
            "Une fenetre allumee suffit pour faire un port.",
            "La nuit rassemble les cinq villages en une seule rive.",
            "Le matin revient en eclats sur les murs colores.",
        ],
        "captions_cn": [
            "珊瑚色的房屋贴着悬崖边缘站立。",
            "小径在葡萄园与峭壁之间向上延伸。",
            "海浪拍来，又把呼吸慢慢收回。",
            "一处阳台静看晚归的小船。",
            "铁轨沿着岩壁的弧线前行。",
            "村庄顺着坡度弯身，姿态从容。",
            "深蓝吞下白昼最后的喧声。",
            "渔网晾晒着，像一面面盐色旗帜。",
            "夕阳在层层梯田后缓慢沉落。",
            "夜幕把铜色涂在屋顶与海浪上。",
            "一扇亮着的窗就足以成为港口。",
            "夜里，五个村庄汇成同一条海岸。",
            "清晨的光碎落在斑斓墙面上。",
        ],
    },
]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_tags(html: str) -> str:
    no_tags = re.sub(r"<[^>]+>", "", html)
    return normalize_space(no_tags)


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "published"}


def simple_slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text).strip("-")
    return slug.lower() or "untitled"


def parse_frontmatter(md_text: str) -> tuple[dict[str, str], str]:
    md_text = md_text.replace("\r\n", "\n")
    if not md_text.startswith("---\n"):
        return {}, md_text

    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", md_text, flags=re.DOTALL)
    if not match:
        return {}, md_text

    raw_meta = match.group(1)
    body = match.group(2)
    meta: dict[str, str] = {}
    for line in raw_meta.split("\n"):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    return meta, body


def build_caption_map(source_dir: Path) -> dict[str, tuple[str, str]]:
    """Load optional captions.csv: filename,caption_fr,caption_cn."""
    mapping: dict[str, tuple[str, str]] = {}
    csv_path = source_dir / "captions.csv"
    if not csv_path.exists():
        return mapping

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = (row.get("filename") or "").strip()
            if not filename:
                continue
            mapping[filename] = (
                (row.get("caption_fr") or "").strip(),
                (row.get("caption_cn") or "").strip(),
            )
    return mapping


def captions_from_filename(filename: str) -> tuple[str, str]:
    """
    Parse captions from filename convention:
    - base__fr caption__cn caption.jpg
    - If no delimiter, use stem as French caption and leave Chinese empty.
    """
    stem = Path(filename).stem
    parts = [normalize_space(p.replace("_", " ").replace("-", " ")) for p in stem.split("__")]
    if len(parts) >= 3:
        return parts[1], parts[2]
    if len(parts) == 2:
        return parts[1], ""
    return normalize_space(stem.replace("_", " ").replace("-", " ")), ""


def parse_nice_album_from_travel(travel_path: Path) -> dict[str, Any] | None:
    if not travel_path.exists():
        return None

    html = travel_path.read_text(encoding="utf-8")
    section_match = re.search(
        r'<section[^>]*id="south-of-france"[^>]*>(.*?)</section>',
        html,
        flags=re.DOTALL,
    )
    if not section_match:
        return None

    section = section_match.group(1)

    title_fr = ""
    title_cn = ""
    h3_match = re.search(r"<h3[^>]*>(.*?)</h3>", section, flags=re.DOTALL)
    if h3_match:
        h3_html = h3_match.group(1)
        cn_match = re.search(r'<span[^>]*class="cn-sub"[^>]*>(.*?)</span>', h3_html, flags=re.DOTALL)
        if cn_match:
            title_cn = strip_tags(cn_match.group(1))
            h3_html = re.sub(r'<span[^>]*class="cn-sub"[^>]*>.*?</span>', "", h3_html, flags=re.DOTALL)
        title_fr = strip_tags(h3_html)

    desc_fr = ""
    desc_cn = ""
    desc_match = re.search(r'<p[^>]*class="sf-description"[^>]*>(.*?)</p>', section, flags=re.DOTALL)
    if desc_match:
        desc_html = desc_match.group(1)
        cn_desc_match = re.search(
            r'<span[^>]*class="cn-paragraph"[^>]*>(.*?)</span>',
            desc_html,
            flags=re.DOTALL,
        )
        if cn_desc_match:
            desc_cn = strip_tags(cn_desc_match.group(1))
            desc_html = re.sub(
                r'<span[^>]*class="cn-paragraph"[^>]*>.*?</span>',
                "",
                desc_html,
                flags=re.DOTALL,
            )
        desc_fr = strip_tags(desc_html)

    cover_url = ""
    cover_match = re.search(r'<img[^>]*class="sf-cover-image"[^>]*src="([^"]+)"', section)
    if cover_match:
        cover_url = cover_match.group(1).strip()

    photos: list[dict[str, Any]] = []
    figure_blocks = re.findall(r'<figure[^>]*class="photo-card[^>]*>(.*?)</figure>', section, flags=re.DOTALL)
    for idx, fig in enumerate(figure_blocks):
        img_match = re.search(r'<img[^>]*class="js-lazy-photo"[^>]*src="([^"]+)"', fig)
        if not img_match:
            continue
        url = img_match.group(1).strip()

        cap_fr = ""
        cap_cn = ""
        cap_match = re.search(r"<figcaption>(.*?)</figcaption>", fig, flags=re.DOTALL)
        if cap_match:
            cap_html = cap_match.group(1)
            cn_cap_match = re.search(r'<span[^>]*class="cn-caption"[^>]*>(.*?)</span>', cap_html, flags=re.DOTALL)
            if cn_cap_match:
                cap_cn = strip_tags(cn_cap_match.group(1))
                cap_html = re.sub(r'<span[^>]*class="cn-caption"[^>]*>.*?</span>', "", cap_html, flags=re.DOTALL)
            cap_fr = strip_tags(cap_html)

        photos.append(
            {
                "url": url,
                "caption_fr": cap_fr,
                "caption_cn": cap_cn,
                "order": idx,
            }
        )

    if not title_fr and not title_cn and not photos:
        return None

    return {
        "title_fr": title_fr or "Nice: Blue Horizon",
        "title_cn": title_cn or "尼斯：蓝色地平线",
        "desc_fr": desc_fr,
        "desc_cn": desc_cn,
        "cover_url": cover_url,
        "photos": photos,
    }


def seed_album_and_photos(db, travel_html_path: Path, dry_run: bool = False) -> tuple[int, int, int]:
    parsed = parse_nice_album_from_travel(travel_html_path)
    if not parsed:
        print(f"[WARN] Could not parse south-of-france section from {travel_html_path}")
        return 0, 0, 0

    album = (
        db.query(Album)
        .filter(Album.title_fr == parsed["title_fr"], Album.title_cn == parsed["title_cn"])
        .first()
    )

    created_album = 0
    if not album:
        album = Album(
            title_fr=parsed["title_fr"],
            title_cn=parsed["title_cn"],
            desc_fr=parsed["desc_fr"],
            desc_cn=parsed["desc_cn"],
            cover_url=parsed["cover_url"],
        )
        db.add(album)
        if not dry_run:
            db.flush()
        created_album = 1

    inserted_photos = 0
    skipped_photos = 0

    for photo_data in parsed["photos"]:
        exists = db.query(Photo).filter(Photo.url == photo_data["url"]).first()
        if exists:
            skipped_photos += 1
            continue

        photo = Photo(
            album_id=album.id if album.id else 0,
            url=photo_data["url"],
            caption_fr=photo_data["caption_fr"],
            caption_cn=photo_data["caption_cn"],
            order=photo_data["order"],
        )

        if dry_run:
            inserted_photos += 1
            continue

        if photo.album_id == 0:
            db.flush()
            photo.album_id = album.id

        db.add(photo)
        inserted_photos += 1

    return created_album, inserted_photos, skipped_photos


def seed_articles_from_posts(db, posts_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    if not posts_dir.exists() or not posts_dir.is_dir():
        print(f"[WARN] posts directory not found: {posts_dir}")
        return 0, 0

    created = 0
    skipped = 0

    for md_file in sorted(posts_dir.glob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)

        slug = meta.get("slug") or simple_slugify(md_file.stem)
        exists = db.query(Article).filter(Article.slug == slug).first()
        if exists:
            skipped += 1
            continue

        title = meta.get("title") or md_file.stem.replace("-", " ").replace("_", " ").strip()
        summary = meta.get("summary") or normalize_space(body)[:180]
        cover_url = meta.get("cover_url") or meta.get("cover") or ""
        is_published = parse_bool(meta.get("is_published"), default=True)

        article = Article(
            title=title or slug,
            slug=slug,
            summary=summary,
            content=body.strip(),
            cover_url=cover_url,
            is_published=is_published,
        )

        if not dry_run:
            db.add(article)
        created += 1

    return created, skipped


def get_or_create_category(
    db,
    slug: str,
    name_fr: str,
    name_cn: str,
    description: str = "",
    layout_type: str = "gallery",
    dry_run: bool = False,
) -> tuple[Category, int]:
    category = db.query(Category).filter(Category.slug == slug).first()
    if category:
        return category, 0

    category = Category(
        slug=slug,
        name_fr=name_fr,
        name_cn=name_cn,
        description=description,
        layout_type=layout_type,
    )
    db.add(category)
    if not dry_run:
        db.flush()
    return category, 1


def seed_voyage_albums_with_placeholders(db, dry_run: bool = False) -> tuple[int, int, int, int]:
    voyage_category, _ = get_or_create_category(
        db=db,
        slug="voyage",
        name_fr="Voyage",
        name_cn="旅行",
        description="Voyage 旅行",
        layout_type="gallery",
        dry_run=dry_run,
    )

    album_specs = [
        {
            "title_fr": "Provence, France",
            "title_cn": "普罗旺斯：薰衣草之乡",
            "desc_fr": "Lavender fields, limestone villages, and warm Mediterranean light.",
            "desc_cn": "薰衣草田、石灰岩村庄与地中海暖光交织成夏日风景。",
            "captions": [
                ("Misty dawn over the lavender rows.", "薄雾晨光掠过薰衣草的整齐纹理。"),
                ("A quiet hilltop village in honey-colored stone.", "蜜色石墙构成的山顶小镇安静伫立。"),
                ("Golden hour on the roads of Provence.", "普罗旺斯乡间公路迎来金色时刻。"),
            ],
        },
        {
            "title_fr": "Bordighera, Italie",
            "title_cn": "博尔迪盖拉：意式边境",
            "desc_fr": "Palm-lined promenades and the soft frontier breeze between sea and hills.",
            "desc_cn": "棕榈步道与海风在丘陵与海岸之间交汇，边境气息温柔而鲜明。",
            "captions": [
                ("Seafront promenade under the afternoon sun.", "午后阳光照亮海滨散步道。"),
                ("Old alleys climbing toward the ridge.", "老城巷道沿坡而上，通往山脊。"),
                ("Evening color over the Ligurian coast.", "利古里亚海岸在黄昏中渐染层次。"),
            ],
        },
        {
            "title_fr": "Cinque Terre, Italie",
            "title_cn": "五渔村：悬崖上的斑斓",
            "desc_fr": "Colorful cliff villages, terraces, and a restless blue sea.",
            "desc_cn": "彩色村落悬于峭壁，梯田与海浪共同构成五渔村的节奏。",
            "captions": [
                ("Pastel houses stacked above the harbor.", "港湾上方层叠的彩色屋檐。"),
                ("A cliff trail opening to a wide blue horizon.", "悬崖步道尽头豁然见海。"),
                ("Night lights reflecting on the sheltered bay.", "夜色灯火映在宁静海湾。"),
            ],
        },
    ]

    albums_created = 0
    photos_created = 0
    photos_skipped = 0

    for spec in album_specs:
        album = (
            db.query(Album)
            .filter(Album.title_fr == spec["title_fr"], Album.title_cn == spec["title_cn"])
            .first()
        )

        if not album:
            album = Album(
                title_fr=spec["title_fr"],
                title_cn=spec["title_cn"],
                desc_fr=spec["desc_fr"],
                desc_cn=spec["desc_cn"],
                category_id=voyage_category.id if voyage_category.id else None,
                cover_url="media/placeholder.jpg",
            )
            db.add(album)
            albums_created += 1
            if not dry_run:
                db.flush()
        else:
            if not album.category_id and voyage_category.id:
                album.category_id = voyage_category.id
            if not album.cover_url:
                album.cover_url = "media/placeholder.jpg"

        for index, (caption_fr, caption_cn) in enumerate(spec["captions"]):
            if not album.id and dry_run:
                photos_created += 1
                continue

            exists = (
                db.query(Photo)
                .filter(
                    Photo.album_id == album.id,
                    Photo.url == "media/placeholder.jpg",
                    Photo.order == index,
                )
                .first()
            )
            if exists:
                photos_skipped += 1
                continue

            photo = Photo(
                album_id=album.id if album.id else 0,
                url="media/placeholder.jpg",
                caption_fr=caption_fr,
                caption_cn=caption_cn,
                order=index,
            )
            if not dry_run:
                if photo.album_id == 0:
                    db.flush()
                    photo.album_id = album.id
                db.add(photo)
            photos_created += 1

    return albums_created, photos_created, photos_skipped, len(album_specs)


def caption_from_sequence(spec: dict[str, Any], sequence: int) -> tuple[str, str]:
    captions_fr: list[str] = spec["captions_fr"]
    captions_cn: list[str] = spec["captions_cn"]
    if sequence <= 0:
        sequence = 1
    idx = (sequence - 1) % len(captions_fr)
    return captions_fr[idx], captions_cn[idx]


def extract_sequence_from_name(filename: str) -> int:
    stem = Path(filename).stem
    match = re.search(r"(\d+)$", stem)
    if not match:
        return 1
    return int(match.group(1))


def find_voyage_media_files() -> list[Path]:
    candidates = [ROOT_DIR / "static" / "media", ROOT_DIR / "media"]
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}
    results: list[Path] = []
    for directory in candidates:
        if not directory.exists() or not directory.is_dir():
            continue
        for file in sorted(directory.iterdir()):
            if file.is_file() and file.suffix.lower() in image_exts:
                results.append(file)
    return results


def seed_voyage_albums_from_media(db, dry_run: bool = False) -> tuple[int, int, int, int]:
    voyage_category, _ = get_or_create_category(
        db=db,
        slug="voyage",
        name_fr="Voyage",
        name_cn="旅行",
        description="Voyage 旅行",
        layout_type="gallery",
        dry_run=dry_run,
    )

    files = find_voyage_media_files()
    albums_created = 0
    photos_created = 0
    photos_skipped = 0

    for spec in VOYAGE_MEDIA_SPECS:
        album = (
            db.query(Album)
            .filter(Album.title_fr == spec["title_fr"], Album.title_cn == spec["title_cn"])
            .first()
        )

        if not album:
            album = Album(
                title_fr=spec["title_fr"],
                title_cn=spec["title_cn"],
                desc_fr=spec["desc_fr"],
                desc_cn=spec["desc_cn"],
                category_id=voyage_category.id if voyage_category.id else None,
                cover_url="",
            )
            db.add(album)
            albums_created += 1
            if not dry_run:
                db.flush()
        else:
            if not album.category_id and voyage_category.id:
                album.category_id = voyage_category.id

        matched_files = [
            path for path in files
            if any(path.name.lower().startswith(prefix) for prefix in spec["prefixes"])
        ]
        matched_files.sort(key=lambda p: extract_sequence_from_name(p.name))

        if matched_files:
            rel_cover = str(matched_files[0].relative_to(ROOT_DIR)).replace("\\", "/")
            # Keep album cover aligned with the first chronological photo.
            album.cover_url = rel_cover

        for path in matched_files:
            rel_url = str(path.relative_to(ROOT_DIR)).replace("\\", "/")
            sequence = extract_sequence_from_name(path.name)
            caption_fr, caption_cn = caption_from_sequence(spec, sequence)
            order_value = sequence - 1 if sequence > 0 else 0

            exists = db.query(Photo).filter(Photo.url == rel_url).first()
            if exists:
                changed = False
                if exists.album_id != album.id and album.id:
                    exists.album_id = album.id
                    changed = True
                if exists.order != order_value:
                    exists.order = order_value
                    changed = True
                if exists.caption_fr != caption_fr:
                    exists.caption_fr = caption_fr
                    changed = True
                if exists.caption_cn != caption_cn:
                    exists.caption_cn = caption_cn
                    changed = True
                if changed:
                    photos_created += 1
                else:
                    photos_skipped += 1
                continue

            photo = Photo(
                album_id=album.id if album.id else 0,
                url=rel_url,
                caption_fr=caption_fr,
                caption_cn=caption_cn,
                order=order_value,
            )

            if not dry_run:
                if photo.album_id == 0:
                    db.flush()
                    photo.album_id = album.id
                db.add(photo)
            photos_created += 1

    return albums_created, photos_created, photos_skipped, len(VOYAGE_MEDIA_SPECS)


def get_or_create_album(
    db,
    title_fr: str,
    title_cn: str,
    desc_fr: str = "",
    desc_cn: str = "",
    cover_url: str = "",
    dry_run: bool = False,
) -> tuple[Album, int]:
    album = db.query(Album).filter(Album.title_fr == title_fr, Album.title_cn == title_cn).first()
    if album:
        return album, 0

    album = Album(
        title_fr=title_fr,
        title_cn=title_cn,
        desc_fr=desc_fr,
        desc_cn=desc_cn,
        cover_url=cover_url,
    )
    db.add(album)
    if not dry_run:
        db.flush()
    return album, 1


def sync_photos_to_static_media(
    db,
    source_dir: Path,
    static_media_dir: Path,
    album_title_fr: str,
    album_title_cn: str,
    dry_run: bool = False,
) -> tuple[int, int, int, int, int]:
    """
    Returns:
    - album_created
    - copied_files
    - skipped_copy_existing
    - inserted_photos
    - skipped_photo_duplicates
    """
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"[WARN] source photos directory not found: {source_dir}")
        return 0, 0, 0, 0, 0

    if not dry_run:
        static_media_dir.mkdir(parents=True, exist_ok=True)

    caption_map = build_caption_map(source_dir)
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}
    source_files = [p for p in sorted(source_dir.iterdir()) if p.is_file() and p.suffix.lower() in image_exts]

    if not source_files:
        print(f"[WARN] no images found in: {source_dir}")
        return 0, 0, 0, 0, 0

    album, album_created = get_or_create_album(
        db=db,
        title_fr=album_title_fr,
        title_cn=album_title_cn,
        dry_run=dry_run,
    )

    copied_files = 0
    skipped_copy_existing = 0
    inserted_photos = 0
    skipped_photo_duplicates = 0

    for index, src in enumerate(source_files):
        dst = static_media_dir / src.name
        rel_url = str(dst.relative_to(ROOT_DIR)).replace("\\", "/")

        if dst.exists():
            skipped_copy_existing += 1
        else:
            if not dry_run:
                shutil.copy2(src, dst)
            copied_files += 1

        exists = db.query(Photo).filter(Photo.url == rel_url).first()
        if exists:
            skipped_photo_duplicates += 1
            continue

        if src.name in caption_map:
            caption_fr, caption_cn = caption_map[src.name]
        else:
            caption_fr, caption_cn = captions_from_filename(src.name)

        photo = Photo(
            album_id=album.id if album.id else 0,
            url=rel_url,
            caption_fr=caption_fr,
            caption_cn=caption_cn,
            order=index,
        )

        if not dry_run:
            if photo.album_id == 0:
                db.flush()
                photo.album_id = album.id
            db.add(photo)
        inserted_photos += 1

    if not dry_run and album.cover_url == "" and source_files:
        first_rel = str((static_media_dir / source_files[0].name).relative_to(ROOT_DIR)).replace("\\", "/")
        album.cover_url = first_rel

    return album_created, copied_files, skipped_copy_existing, inserted_photos, skipped_photo_duplicates


def resolve_posts_dir(preferred: Path) -> Path:
    if preferred.exists() and preferred.is_dir():
        return preferred

    fallback = ROOT_DIR / "articles"
    if fallback.exists() and fallback.is_dir():
        return fallback

    return preferred


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SQLite data.db using local travel/posts content")
    parser.add_argument("--travel-html", default=str(ROOT_DIR / "travel.html"), help="Path to travel.html")
    parser.add_argument("--posts-dir", default=str(ROOT_DIR / "posts"), help="Path to posts directory")
    parser.add_argument(
        "--source-photos-dir",
        default="",
        help="Optional source photos directory to sync into static/media",
    )
    parser.add_argument(
        "--static-media-dir",
        default=str(ROOT_DIR / "static" / "media"),
        help="Target static media directory (default: ./static/media)",
    )
    parser.add_argument(
        "--sync-album-title-fr",
        default="Synced Originals",
        help="Album title (French) for synced source photos",
    )
    parser.add_argument(
        "--sync-album-title-cn",
        default="同步原图",
        help="Album title (Chinese) for synced source photos",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse and print counts without writing DB")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    posts_dir = resolve_posts_dir(Path(args.posts_dir))

    db = SessionLocal()
    try:
        album_created, photos_created, photos_skipped = seed_album_and_photos(
            db=db,
            travel_html_path=Path(args.travel_html),
            dry_run=args.dry_run,
        )

        articles_created, articles_skipped = seed_articles_from_posts(
            db=db,
            posts_dir=posts_dir,
            dry_run=args.dry_run,
        )

        voyage_albums_created, voyage_photos_created, voyage_photos_skipped, voyage_albums_target = (
            seed_voyage_albums_from_media(
                db=db,
                dry_run=args.dry_run,
            )
        )

        sync_album_created = 0
        copied_files = 0
        skipped_copy_existing = 0
        synced_photos_created = 0
        synced_photos_skipped = 0

        if args.source_photos_dir.strip():
            (
                sync_album_created,
                copied_files,
                skipped_copy_existing,
                synced_photos_created,
                synced_photos_skipped,
            ) = sync_photos_to_static_media(
                db=db,
                source_dir=Path(args.source_photos_dir),
                static_media_dir=Path(args.static_media_dir),
                album_title_fr=args.sync_album_title_fr,
                album_title_cn=args.sync_album_title_cn,
                dry_run=args.dry_run,
            )

        if args.dry_run:
            db.rollback()
        else:
            db.commit()

        print("\nSeed completed")
        print(f"- album created: {album_created}")
        print(f"- photos created: {photos_created}")
        print(f"- photos skipped (duplicate url): {photos_skipped}")
        print(f"- markdown source: {posts_dir}")
        print(f"- articles created: {articles_created}")
        print(f"- articles skipped (duplicate slug): {articles_skipped}")
        print(f"- voyage placeholder albums target: {voyage_albums_target}")
        print(f"- voyage albums created: {voyage_albums_created}")
        print(f"- voyage placeholder photos created: {voyage_photos_created}")
        print(f"- voyage placeholder photos skipped: {voyage_photos_skipped}")
        print(f"- sync album created: {sync_album_created}")
        print(f"- files copied to static/media: {copied_files}")
        print(f"- files already existed in static/media: {skipped_copy_existing}")
        print(f"- synced photos created: {synced_photos_created}")
        print(f"- synced photos skipped (duplicate url): {synced_photos_skipped}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
