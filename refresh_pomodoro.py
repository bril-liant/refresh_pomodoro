# 필요한 라이브러리들을 가져옵니다.
import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import json  # 설정 저장/불러오기를 위한 json 모듈
import os  # 운영체제 관련 기능 사용 (파일 경로 등)
import sys  # 실행 파일 경로 확인용

# --- 스타일 색상 (유지) ---
COLOR_BACKGROUND = "#15202B"
COLOR_TEXT = "#FFFFFF"
COLOR_INPUT_BG = "#1E2732"
COLOR_INPUT_FG = "#FFFFFF"
COLOR_BUTTON = "#1DA1F2"
COLOR_INPUT_BORDER = "#556677"
COLOR_INPUT_FOCUS_BORDER = COLOR_BUTTON
COLOR_BUTTON_TEXT = "#FFFFFF"
COLOR_BUTTON_ACTIVE = "#1A91DA"
COLOR_LABEL_MUTED = "#8899A6"
COLOR_SECTION_BG = "#192734"
COLOR_SECTION_TITLE_BG = "#203A4C"
COLOR_CHECK_TEXT = "#E1E8ED"

FONT_FAMILY = "맑은 고딕"
FONT_SIZE_SMALL = 9
FONT_SIZE_NORMAL = 10
FONT_SIZE_MEDIUM = 11
FONT_SIZE_LARGE_STATUS = 13
FONT_SIZE_TIMER = 28
FONT_SIZE_BUTTON = 10
FONT_SIZE_COLLAPSIBLE_TITLE = FONT_SIZE_LARGE_STATUS

FONT_SIZE_OVERLAY_MESSAGE = 22
FONT_SIZE_OVERLAY_TIME = 30
FONT_SIZE_OVERLAY_CLICK_PROMPT = FONT_SIZE_NORMAL

CHECK_CHAR = "✓"
UNCHECK_CHAR = "☐"

MEAL_CHECK_INTERVAL_MS = 10000
SETTINGS_FILENAME = "refresh_pomodoro_settings.json"  # 설정 파일 이름 변경
APP_NAME_FOR_SETTINGS = "RefreshPomodoro"  # 설정 폴더 이름 변경


def get_settings_path():
    """설정 파일 경로를 반환합니다. (OS별 사용자 데이터 폴더 우선)"""
    if sys.platform == "win32":
        path = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME_FOR_SETTINGS
        )
    elif sys.platform == "darwin":  # macOS
        path = os.path.join(
            os.path.expanduser("~"),
            "Library",
            "Application Support",
            APP_NAME_FOR_SETTINGS,
        )
    else:  # Linux 등 기타
        path = os.path.join(
            os.environ.get(
                "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
            ),
            APP_NAME_FOR_SETTINGS,
        )

    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)  # exist_ok=True 추가
        except OSError:
            if getattr(sys, "frozen", False):
                path = os.path.dirname(sys.executable)
            else:
                path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(path, SETTINGS_FILENAME)

    return os.path.join(path, SETTINGS_FILENAME)


class CollapsibleFrame(tk.Frame):
    def __init__(
        self,
        parent,
        text="",
        initial_collapsed=False,
        bg_color=COLOR_BACKGROUND,
        title_bg=COLOR_BACKGROUND,
        title_fg=COLOR_TEXT,
        content_bg=COLOR_BACKGROUND,
        on_toggle=None,
        font_size_title=FONT_SIZE_COLLAPSIBLE_TITLE,
    ):
        super().__init__(parent, bg=bg_color)
        self.parent_root = parent.winfo_toplevel()
        self.on_toggle = on_toggle
        self._is_collapsed = initial_collapsed
        self.title_frame = tk.Frame(
            self, relief=tk.FLAT, bd=0, bg=title_bg, padx=5, pady=2
        )
        self.title_frame.pack(fill=tk.X)
        self.title_frame.bind("<Button-1>", lambda e: self.toggle())
        self.toggle_button_text = tk.StringVar()
        self.toggle_button_text.set("▼ " if not self._is_collapsed else "▶ ")
        self.toggle_button = tk.Label(
            self.title_frame,
            textvariable=self.toggle_button_text,
            font=(FONT_FAMILY, font_size_title, "bold"),
            bg=title_bg,
            fg=title_fg,
            width=2,
            anchor="w",
        )
        self.toggle_button.pack(side=tk.LEFT)
        self.toggle_button.bind("<Button-1>", lambda e: self.toggle())
        self.title_label = tk.Label(
            self.title_frame,
            text=text,
            font=(FONT_FAMILY, font_size_title, "bold"),
            bg=title_bg,
            fg=title_fg,
            anchor="w",
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.title_label.bind("<Button-1>", lambda e: self.toggle())
        self.content_frame = tk.Frame(
            self, relief=tk.FLAT, bd=0, bg=content_bg, padx=0, pady=0
        )
        if not self._is_collapsed:
            self.content_frame.pack(fill=tk.X)

    def toggle(self):
        self._is_collapsed = not self._is_collapsed
        if self._is_collapsed:
            self.content_frame.pack_forget()
            self.toggle_button_text.set("▶ ")
        else:
            self.content_frame.pack(fill=tk.X)
            self.toggle_button_text.set("▼ ")
        if self.on_toggle:
            self.on_toggle()

    def get_content_frame(self):
        return self.content_frame


class CustomCheckbutton(tk.Frame):
    def __init__(
        self, parent, variable, text="", command=None, description="", **kwargs
    ):
        super().__init__(parent, bg=kwargs.get("bg", COLOR_SECTION_BG))
        self.variable = variable
        self.command = command
        self._text_content = text
        self.check_text_var = tk.StringVar()
        # _text_content가 설정된 후 update_symbol 호출 보장
        # variable의 trace 콜백에서 초기 심볼 업데이트를 하므로 여기서 직접 호출할 필요는 없을 수 있음
        # 단, variable이 아직 설정되지 않은 상태에서 trace가 바로 동작하지 않을 수 있으므로,
        # 생성자 마지막에 한 번 호출하거나, variable 설정 후 명시적 호출을 고려.
        # 여기서는 variable이 외부에서 생성되어 전달되므로, trace가 잘 동작할 것으로 기대.
        # 하지만 안전하게 초기 표시를 위해 호출.
        self.update_symbol()
        self.button = tk.Label(
            self,
            textvariable=self.check_text_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            fg=COLOR_CHECK_TEXT,
            bg=self.cget("bg"),
            anchor="w",
            cursor="hand2",
        )
        self.button.pack(side=tk.LEFT, pady=0)
        self.button.bind("<Button-1>", self.toggle)

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())
        if self.command and callable(self.command):
            self.command()

    def update_symbol(self):  # BooleanVar의 trace에 의해 호출됨
        char = CHECK_CHAR if self.variable.get() else UNCHECK_CHAR
        self.check_text_var.set(f"{char} {self._text_content}")


class PomodoroApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("리프레시 뽀모도로")  # 프로그램 이름 변경
        self.root.configure(bg=COLOR_BACKGROUND)
        self.settings_path = get_settings_path()

        self.work_minutes_default = 25
        self.rest_minutes_default = 5
        self.always_on_top_default = False
        self.force_rest_default = True
        self.use_meal_alert_default = True
        self.use_long_rest_suggestion_default = True
        self.meal_times_default = {"점심": "12:00", "저녁": "17:30"}
        self.long_rest_cycle_default = "4"
        self.long_rest_duration_default = "15"

        self.current_mode = "준비"
        self.remaining_seconds = 0
        self.timer_id = None
        self.is_running = False
        self.overlay_window = None
        self.total_work_seconds_today = 0
        self.last_session_work_seconds = 0
        self.pomodoro_cycles_today = 0

        self.always_on_top_var = tk.BooleanVar()
        self.force_rest_var = tk.BooleanVar()
        self.use_meal_alert_var = tk.BooleanVar()
        self.use_long_rest_suggestion_var = tk.BooleanVar()
        self.long_rest_cycle_threshold_var = tk.StringVar()
        self.long_rest_duration_var = tk.StringVar()
        self.meal_times_vars = {
            name: tk.StringVar() for name in self.meal_times_default
        }
        self.work_minutes_var = tk.StringVar()
        self.rest_minutes_var = tk.StringVar()

        self.always_on_top_check = None
        self.force_rest_check = None
        self.meal_alert_check = None
        self.long_rest_check = None

        self.load_settings()

        self.always_on_top_var.trace_add(
            "write",
            lambda *args: (
                (
                    self.always_on_top_check.update_symbol()
                    if self.always_on_top_check
                    else None
                ),
                self.toggle_always_on_top_action(),
            ),
        )
        self.force_rest_var.trace_add(
            "write",
            lambda *args: (
                self.force_rest_check.update_symbol() if self.force_rest_check else None
            ),
        )
        self.use_meal_alert_var.trace_add(
            "write",
            lambda *args: (
                (
                    self.meal_alert_check.update_symbol()
                    if self.meal_alert_check
                    else None
                ),
                self.toggle_meal_time_entries_visibility(),
            ),
        )
        self.use_long_rest_suggestion_var.trace_add(
            "write",
            lambda *args: (
                self.long_rest_check.update_symbol() if self.long_rest_check else None,
                self.toggle_long_rest_settings_visibility(),
            ),
        )

        self.meal_alert_shown_today = {meal: False for meal in self.meal_times_default}
        self.today_date = datetime.date.today()

        self.setup_ui()
        self.update_stats_display()
        self.check_meal_time_periodically()
        self.toggle_always_on_top_action()
        self.root.update_idletasks()
        self.adjust_window_size()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def adjust_window_size(self):
        self.root.update_idletasks()

    def setup_ui(self):
        main_frame = tk.Frame(self.root, padx=10, pady=8, bg=COLOR_BACKGROUND)
        main_frame.pack(expand=True, fill=tk.BOTH)
        self.status_label = tk.Label(
            main_frame,
            text="준비됐어요!",
            font=(FONT_FAMILY, FONT_SIZE_LARGE_STATUS, "bold"),
            bg=COLOR_BACKGROUND,
            fg=COLOR_TEXT,
        )
        self.status_label.pack(pady=(5, 1))
        self.time_label = tk.Label(
            main_frame,
            text="00:00",
            font=(FONT_FAMILY, FONT_SIZE_TIMER, "bold"),
            bg=COLOR_BACKGROUND,
            fg=COLOR_TEXT,
        )
        self.time_label.pack(pady=(0, 8))
        buttons_frame = tk.Frame(main_frame, bg=COLOR_BACKGROUND)
        buttons_frame.pack(pady=(0, 10))
        self.start_button = tk.Button(
            buttons_frame,
            text="시작",
            width=8,
            command=self.start_timer,
            bg=COLOR_BUTTON,
            fg=COLOR_BUTTON_TEXT,
            activebackground=COLOR_BUTTON_ACTIVE,
            activeforeground=COLOR_BUTTON_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_BUTTON, "bold"),
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=5,
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = tk.Button(
            buttons_frame,
            text="정지",
            width=8,
            command=self.stop_timer,
            state=tk.DISABLED,
            bg=COLOR_LABEL_MUTED,
            fg=COLOR_BUTTON_TEXT,
            activebackground=COLOR_BUTTON_ACTIVE,
            activeforeground=COLOR_BUTTON_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_BUTTON, "bold"),
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=5,
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stats_label = tk.Label(
            main_frame,
            text="오늘 집중 0분 / 뽀모도로 0회",
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=COLOR_BACKGROUND,
            fg=COLOR_LABEL_MUTED,
        )
        self.stats_label.pack(pady=(0, 8), anchor="center")

        self.all_settings_collapsible = CollapsibleFrame(
            main_frame,
            text="설정",
            initial_collapsed=True,
            title_bg=COLOR_BACKGROUND,
            content_bg=COLOR_BACKGROUND,
            on_toggle=self.adjust_window_size,
            font_size_title=FONT_SIZE_COLLAPSIBLE_TITLE,
        )
        self.all_settings_collapsible.pack(fill=tk.X, pady=(0, 3))
        all_settings_content = self.all_settings_collapsible.get_content_frame()

        time_settings_labelframe = ttk.Labelframe(
            all_settings_content, text="시간 설정", style="Custom.TLabelframe"
        )
        time_settings_labelframe.pack(fill=tk.X, pady=(0, 5), padx=5)
        style = ttk.Style()
        style.configure(
            "Custom.TLabelframe",
            background=COLOR_SECTION_BG,
            bordercolor=COLOR_SECTION_BG,
            relief=tk.FLAT,
            padding=(5, 0),
        )
        style.configure(
            "Custom.TLabelframe.Label",
            background=COLOR_SECTION_BG,
            foreground=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_MEDIUM, "bold"),
            padding=(5, 2),
        )

        work_frame = tk.Frame(time_settings_labelframe, bg=COLOR_SECTION_BG)
        work_frame.pack(fill=tk.X, padx=5)
        tk.Label(
            work_frame,
            text="집중 (분):",
            bg=COLOR_SECTION_BG,
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        ).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.work_entry = tk.Entry(
            work_frame,
            width=5,
            textvariable=self.work_minutes_var,
            bg=COLOR_INPUT_BG,
            fg=COLOR_INPUT_FG,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER,
            highlightcolor=COLOR_INPUT_FOCUS_BORDER,
            insertbackground=COLOR_TEXT,
        )
        self.work_entry.grid(row=0, column=1, padx=5, pady=3)
        tk.Label(
            time_settings_labelframe,
            text="한 번 집중할 시간이에요.",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            justify="left",
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(0, 3), anchor="w")
        rest_frame = tk.Frame(time_settings_labelframe, bg=COLOR_SECTION_BG)
        rest_frame.pack(fill=tk.X, padx=5)
        tk.Label(
            rest_frame,
            text="휴식 (분):",
            bg=COLOR_SECTION_BG,
            fg=COLOR_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        ).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.rest_entry = tk.Entry(
            rest_frame,
            width=5,
            textvariable=self.rest_minutes_var,
            bg=COLOR_INPUT_BG,
            fg=COLOR_INPUT_FG,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER,
            highlightcolor=COLOR_INPUT_FOCUS_BORDER,
            insertbackground=COLOR_TEXT,
        )
        self.rest_entry.grid(row=0, column=1, padx=5, pady=3)
        tk.Label(
            time_settings_labelframe,
            text="짧은 휴식으로 뇌를 식혀줘요.",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            justify="left",
            anchor="w",
        ).pack(fill=tk.X, padx=10, pady=(0, 3), anchor="w")

        additional_settings_labelframe = ttk.Labelframe(
            all_settings_content, text="추가 기능", style="Custom.TLabelframe"
        )
        additional_settings_labelframe.pack(fill=tk.X, pady=5, padx=5)

        def create_setting_option(parent, variable, text, description, command=None):
            option_frame = tk.Frame(parent, bg=COLOR_SECTION_BG)
            option_frame.pack(fill=tk.X, pady=1, padx=5)
            check_btn = CustomCheckbutton(
                option_frame,
                variable=variable,
                text=text,
                command=command,
                bg=COLOR_SECTION_BG,
            )
            check_btn.pack(anchor="w")
            desc_label = tk.Label(
                option_frame,
                text=description,
                font=(FONT_FAMILY, FONT_SIZE_SMALL),
                fg=COLOR_LABEL_MUTED,
                bg=COLOR_SECTION_BG,
                justify="left",
                anchor="w",
                wraplength=300,
            )
            desc_label.pack(fill=tk.X, padx=25, pady=(0, 3), anchor="w")
            return check_btn

        self.always_on_top_check = create_setting_option(
            additional_settings_labelframe,
            self.always_on_top_var,
            "항상 맨 위에 표시",
            "앱을 다른 창들보다 항상 위에 보여줘요.",
            None,
        )
        self.force_rest_check = create_setting_option(
            additional_settings_labelframe,
            self.force_rest_var,
            "강제로 휴식하기",
            "휴식 시간엔 아무것도 작업할 수 없게 화면을 가려요!",
            None,
        )
        self.meal_alert_check = create_setting_option(
            additional_settings_labelframe,
            self.use_meal_alert_var,
            "식사 시간 알림",
            "밥 때 되면 알려줘서 끼니를 챙겨줘요.",
            None,
        )
        self.long_rest_check = create_setting_option(
            additional_settings_labelframe,
            self.use_long_rest_suggestion_var,
            "긴 휴식 제안",
            "집중 세션을 여러 번 마치면 긴 휴식을 추천해줘요.",
            None,
        )

        self.long_rest_settings_frame = tk.Frame(
            additional_settings_labelframe, bg=COLOR_SECTION_BG
        )
        tk.Label(
            self.long_rest_settings_frame,
            text="몇 번마다:",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        ).grid(row=0, column=0, padx=5, sticky="w", pady=(0, 2))
        self.long_rest_cycle_entry = tk.Entry(
            self.long_rest_settings_frame,
            textvariable=self.long_rest_cycle_threshold_var,
            width=4,
            bg=COLOR_INPUT_BG,
            fg=COLOR_INPUT_FG,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER,
            highlightcolor=COLOR_INPUT_FOCUS_BORDER,
            insertbackground=COLOR_TEXT,
        )
        self.long_rest_cycle_entry.grid(row=0, column=1, padx=5, pady=(0, 2))
        tk.Label(
            self.long_rest_settings_frame,
            text="회",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        ).grid(row=0, column=2, sticky="w")
        tk.Label(
            self.long_rest_settings_frame,
            text="몇 분씩 추천:",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        ).grid(row=1, column=0, padx=5, sticky="w")
        self.long_rest_duration_entry = tk.Entry(
            self.long_rest_settings_frame,
            textvariable=self.long_rest_duration_var,
            width=4,
            bg=COLOR_INPUT_BG,
            fg=COLOR_INPUT_FG,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER,
            highlightcolor=COLOR_INPUT_FOCUS_BORDER,
            insertbackground=COLOR_TEXT,
        )
        self.long_rest_duration_entry.grid(row=1, column=1, padx=5)
        tk.Label(
            self.long_rest_settings_frame,
            text="분",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        ).grid(row=1, column=2, sticky="w")
        self.toggle_long_rest_settings_visibility()

        self.meal_entries_frame = tk.Frame(
            additional_settings_labelframe, bg=COLOR_SECTION_BG
        )
        tk.Label(
            self.meal_entries_frame,
            text="점심:",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        ).grid(row=0, column=0, padx=5, sticky="w", pady=(0, 2))
        self.lunch_time_entry = tk.Entry(
            self.meal_entries_frame,
            textvariable=self.meal_times_vars["점심"],
            width=6,
            bg=COLOR_INPUT_BG,
            fg=COLOR_INPUT_FG,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER,
            highlightcolor=COLOR_INPUT_FOCUS_BORDER,
            insertbackground=COLOR_TEXT,
        )
        self.lunch_time_entry.grid(row=0, column=1, padx=5, pady=(0, 2))
        tk.Label(
            self.meal_entries_frame,
            text="저녁:",
            bg=COLOR_SECTION_BG,
            fg=COLOR_LABEL_MUTED,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
        ).grid(row=1, column=0, padx=5, sticky="w")
        self.dinner_time_entry = tk.Entry(
            self.meal_entries_frame,
            textvariable=self.meal_times_vars["저녁"],
            width=6,
            bg=COLOR_INPUT_BG,
            fg=COLOR_INPUT_FG,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER,
            highlightcolor=COLOR_INPUT_FOCUS_BORDER,
            insertbackground=COLOR_TEXT,
        )
        self.dinner_time_entry.grid(row=1, column=1, padx=5)
        self.toggle_meal_time_entries_visibility()

    def load_settings(self):
        try:
            with open(self.settings_path, "r") as f:
                settings = json.load(f)
            self.work_minutes_var.set(
                settings.get("work_minutes", str(self.work_minutes_default))
            )
            self.rest_minutes_var.set(
                settings.get("rest_minutes", str(self.rest_minutes_default))
            )
            self.always_on_top_var.set(
                settings.get("always_on_top", self.always_on_top_default)
            )
            self.force_rest_var.set(settings.get("force_rest", self.force_rest_default))
            self.use_meal_alert_var.set(
                settings.get("use_meal_alert", self.use_meal_alert_default)
            )
            loaded_meal_times = settings.get("meal_times", self.meal_times_default)
            for meal_name, default_time in self.meal_times_default.items():
                self.meal_times_vars[meal_name].set(
                    loaded_meal_times.get(meal_name, default_time)
                )
            self.use_long_rest_suggestion_var.set(
                settings.get(
                    "use_long_rest_suggestion", self.use_long_rest_suggestion_default
                )
            )
            self.long_rest_cycle_threshold_var.set(
                settings.get("long_rest_cycle_threshold", self.long_rest_cycle_default)
            )
            self.long_rest_duration_var.set(
                settings.get("long_rest_duration", self.long_rest_duration_default)
            )
            if settings.get("last_saved_date") == str(datetime.date.today()):
                self.total_work_seconds_today = settings.get(
                    "total_work_seconds_today", 0
                )
                self.pomodoro_cycles_today = settings.get("pomodoro_cycles_today", 0)
            else:  # 날짜가 다르면 통계 초기화
                self.total_work_seconds_today = 0
                self.pomodoro_cycles_today = 0
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            TypeError,
        ):  # TypeError 추가 (키 부재 시 기본값 처리 위함)
            self.work_minutes_var.set(str(self.work_minutes_default))
            self.rest_minutes_var.set(str(self.rest_minutes_default))
            self.always_on_top_var.set(self.always_on_top_default)
            self.force_rest_var.set(self.force_rest_default)
            self.use_meal_alert_var.set(self.use_meal_alert_default)
            for meal_name, default_time in self.meal_times_default.items():
                self.meal_times_vars[meal_name].set(default_time)
            self.use_long_rest_suggestion_var.set(self.use_long_rest_suggestion_default)
            self.long_rest_cycle_threshold_var.set(self.long_rest_cycle_default)
            self.long_rest_duration_var.set(self.long_rest_duration_default)
            self.total_work_seconds_today = 0
            self.pomodoro_cycles_today = 0

    def save_settings(self):
        settings = {
            "work_minutes": self.work_minutes_var.get(),
            "rest_minutes": self.rest_minutes_var.get(),
            "always_on_top": self.always_on_top_var.get(),
            "force_rest": self.force_rest_var.get(),
            "use_meal_alert": self.use_meal_alert_var.get(),
            "meal_times": {
                name: var.get() for name, var in self.meal_times_vars.items()
            },
            "use_long_rest_suggestion": self.use_long_rest_suggestion_var.get(),
            "long_rest_cycle_threshold": self.long_rest_cycle_threshold_var.get(),
            "long_rest_duration": self.long_rest_duration_var.get(),
            "total_work_seconds_today": self.total_work_seconds_today,
            "pomodoro_cycles_today": self.pomodoro_cycles_today,
            "last_saved_date": str(datetime.date.today()),
        }
        try:
            with open(self.settings_path, "w") as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            # 사용자에게 오류를 알리는 대신 콘솔에만 출력하거나 로그 파일에 기록할 수 있습니다.
            # messagebox.showerror("오류", f"설정을 저장하는 데 실패했어요: {e}", parent=self.root) # 필요시 주석 해제
            print(f"설정 저장 중 오류: {e}")

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def update_stats_display(self):
        total_mins = self.total_work_seconds_today // 60
        if total_mins == 0 and self.total_work_seconds_today > 0:
            time_str = f"{self.total_work_seconds_today}초"
        elif total_mins < 60:
            time_str = f"{total_mins}분"
        else:
            hours = total_mins // 60
            mins = total_mins % 60
            time_str = f"{hours}시간 {mins}분"
        cycle_str = f"{self.pomodoro_cycles_today}회"
        self.stats_label.config(text=f"오늘 집중 {time_str} / 뽀모도로 {cycle_str}")

    def update_total_work_time_display(self):
        self.update_stats_display()

    def update_pomodoro_cycle_display(self):
        self.update_stats_display()

    def toggle_always_on_top_action(self, *args):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def toggle_meal_time_entries_visibility(self, *args):
        if self.meal_alert_check:  # 위젯이 생성된 후에만 실행
            if self.use_meal_alert_var.get():
                self.meal_entries_frame.pack(
                    after=self.meal_alert_check.master, fill=tk.X, padx=25, pady=(0, 5)
                )
            else:
                self.meal_entries_frame.pack_forget()
            self.adjust_window_size()

    def toggle_long_rest_settings_visibility(self, *args):
        if self.long_rest_check:  # 위젯이 생성된 후에만 실행
            if self.use_long_rest_suggestion_var.get():
                self.long_rest_settings_frame.pack(
                    after=self.long_rest_check.master, fill=tk.X, padx=25, pady=(0, 5)
                )
            else:
                self.long_rest_settings_frame.pack_forget()
            self.adjust_window_size()

    def validate_positive_integer(self, val_str, field_name="값"):
        try:
            value = int(val_str)
        except ValueError:
            messagebox.showwarning(
                "입력 확인", f"{field_name}에 숫자만 넣어주세요!", parent=self.root
            )
            return None
        if value <= 0:
            messagebox.showwarning(
                "입력 확인", f"{field_name}은 0보다 커야 해요.", parent=self.root
            )
            return None
        return value

    def validate_time_input(self, time_str, field_name="시간"):
        return self.validate_positive_integer(time_str, field_name)

    def validate_cycle_input(self, cycle_str, field_name="횟수"):
        return self.validate_positive_integer(cycle_str, field_name)

    def validate_meal_time_format(self, time_str, meal_name):
        try:
            return datetime.datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            messagebox.showwarning(
                "시간 형식 오류",
                f"{meal_name} 시간은 HH:MM 형식으로 입력해주세요 (예: 12:30).",
                parent=self.root,
            )
            return None

    def start_timer(self):
        if self.is_running:
            return
        work_minutes = self.validate_time_input(
            self.work_minutes_var.get(), "집중 시간"
        )
        rest_minutes = self.validate_time_input(
            self.rest_minutes_var.get(), "휴식 시간"
        )
        if work_minutes is None or rest_minutes is None:
            return

        long_rest_threshold = None
        long_rest_duration = None
        if self.use_long_rest_suggestion_var.get():
            long_rest_threshold = self.validate_cycle_input(
                self.long_rest_cycle_threshold_var.get(), "긴 휴식 반복 횟수"
            )
            long_rest_duration = self.validate_time_input(
                self.long_rest_duration_var.get(), "긴 휴식 추천 시간"
            )
            if long_rest_threshold is None or long_rest_duration is None:
                return

        entry_list_to_disable = [
            self.work_entry,
            self.rest_entry,
            self.lunch_time_entry,
            self.dinner_time_entry,
        ]
        if self.use_long_rest_suggestion_var.get():
            entry_list_to_disable.extend(
                [self.long_rest_cycle_entry, self.long_rest_duration_entry]
            )
        for entry_widget in entry_list_to_disable:
            if entry_widget:
                entry_widget.config(state=tk.DISABLED, fg=COLOR_LABEL_MUTED)

        self.current_mode = "집중"
        self.remaining_seconds = work_minutes * 60
        self.last_session_work_seconds = 0
        self.is_running = True
        self.start_button.config(state=tk.DISABLED, bg=COLOR_LABEL_MUTED)
        self.stop_button.config(state=tk.NORMAL, bg=COLOR_BUTTON)
        self.status_label.config(text=f"집중! 🔥")
        self.update_timer_display()
        self.countdown()

    def countdown(self):
        if not self.is_running or self.remaining_seconds < 0:
            return
        if self.current_mode == "집중":
            self.last_session_work_seconds += 1
        if self.remaining_seconds == 0:
            if self.current_mode == "집중":
                self.total_work_seconds_today += self.last_session_work_seconds
                self.pomodoro_cycles_today += 1
                self.update_stats_display()
                if self.use_long_rest_suggestion_var.get():
                    long_rest_threshold = self.validate_cycle_input(
                        self.long_rest_cycle_threshold_var.get(), "긴 휴식 반복 횟수"
                    )  # 값 다시 가져오기
                    long_rest_duration = self.validate_time_input(
                        self.long_rest_duration_var.get(), "긴 휴식 추천 시간"
                    )  # 값 다시 가져오기
                    if (
                        long_rest_threshold is not None
                        and long_rest_duration is not None
                        and self.pomodoro_cycles_today > 0
                        and self.pomodoro_cycles_today % long_rest_threshold == 0
                    ):
                        if messagebox.askyesno(
                            "긴 휴식 시간!",
                            f"벌써 {self.pomodoro_cycles_today}번째 뽀모도로를 마쳤어요! 대단해요! 👍\n{long_rest_duration}분 동안 긴 휴식을 가져보는 건 어때요?",
                            parent=self.root,
                        ):
                            self.current_mode = "긴 휴식"
                            self.remaining_seconds = long_rest_duration * 60
                            self.status_label.config(text="긴 휴식 중... 😌")
                            self.update_timer_display()
                            self.show_overlay_window(
                                long_rest_duration, is_long_rest=True
                            )
                            return
            self.switch_mode()
        else:
            self.remaining_seconds -= 1
            self.update_timer_display()
            self.timer_id = self.root.after(1000, self.countdown)

    def update_timer_display(self):
        mins, secs = divmod(self.remaining_seconds, 60)
        self.time_label.config(text=f"{mins:02d}:{secs:02d}")

    def switch_mode(self):
        if self.current_mode == "집중":
            self.current_mode = "휴식"
            rest_minutes = self.validate_time_input(
                self.rest_minutes_var.get(), "휴식 시간"
            )
            if rest_minutes is None:
                self.stop_timer()
                messagebox.showerror(
                    "오류 발생",
                    "휴식 시간을 확인해주세요. 타이머를 멈춥니다.",
                    parent=self.root,
                )
                return
            self.remaining_seconds = rest_minutes * 60
            self.status_label.config(text=f"휴식 시간 🧘")
            self.show_overlay_window(rest_minutes)
        elif self.current_mode == "휴식" or self.current_mode == "긴 휴식":
            self.current_mode = "집중"
            work_minutes = self.validate_time_input(
                self.work_minutes_var.get(), "집중 시간"
            )
            if work_minutes is None:
                self.stop_timer()
                messagebox.showerror(
                    "오류 발생",
                    "집중 시간을 확인해주세요. 타이머를 멈춥니다.",
                    parent=self.root,
                )
                return
            self.remaining_seconds = work_minutes * 60
            self.last_session_work_seconds = 0
            self.status_label.config(text=f"집중! 🔥")
            self.update_timer_display()
            if self.is_running:
                self.timer_id = self.root.after(1000, self.countdown)

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        if self.is_running and self.current_mode == "집중":
            self.total_work_seconds_today += self.last_session_work_seconds
            self.update_stats_display()
        self.is_running = False
        self.current_mode = "정지됨"
        self.last_session_work_seconds = 0
        self.status_label.config(text="잠시 멈춤 ⏸️")
        self.start_button.config(state=tk.NORMAL, bg=COLOR_BUTTON)
        self.stop_button.config(state=tk.DISABLED, bg=COLOR_LABEL_MUTED)

        entry_list_to_enable = [
            self.work_entry,
            self.rest_entry,
            self.lunch_time_entry,
            self.dinner_time_entry,
        ]
        if self.use_long_rest_suggestion_var.get():
            entry_list_to_enable.extend(
                [self.long_rest_cycle_entry, self.long_rest_duration_entry]
            )
        for entry_widget in entry_list_to_enable:
            if entry_widget:
                entry_widget.config(state=tk.NORMAL, fg=COLOR_INPUT_FG)

        self.toggle_meal_time_entries_visibility()
        self.toggle_long_rest_settings_visibility()
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            self.overlay_window = None

    def close_overlay_and_start_work(self, event=None, next_mode="집중"):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            self.overlay_window = None
        if next_mode == "집중":
            self.current_mode = "집중"
            work_minutes = self.validate_time_input(
                self.work_minutes_var.get(), "집중 시간"
            )
            if work_minutes is None:
                self.stop_timer()
                messagebox.showerror(
                    "앗!",
                    "집중 시간을 확인해주세요. 타이머를 시작할 수 없어요.",
                    parent=self.root,
                )
                return
            self.remaining_seconds = work_minutes * 60
            self.last_session_work_seconds = 0
            self.status_label.config(text=f"집중! 🔥")
        self.update_timer_display()
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED, bg=COLOR_LABEL_MUTED)
            self.stop_button.config(state=tk.NORMAL, bg=COLOR_BUTTON)
        self.timer_id = self.root.after(1000, self.countdown)

    def show_overlay_window(self, duration_minutes, is_long_rest=False):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
        duration_seconds = duration_minutes * 60
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.attributes("-fullscreen", True)
        self.overlay_window.attributes("-topmost", True)
        self.overlay_window.attributes("-alpha", 0.92)
        self.overlay_window.configure(bg="black")
        if is_long_rest:
            main_message = f"수고했어요! 긴 휴식 시간이에요.\n{duration_minutes}분 동안 편안하게 쉬세요. ☕"
        else:
            main_message = (
                f"쉬는 시간이에요!\n{duration_minutes}분 동안 잠시 쉬어가세요."
            )
        self.overlay_message_label = tk.Label(
            self.overlay_window,
            text=main_message,
            font=(FONT_FAMILY, FONT_SIZE_OVERLAY_MESSAGE, "bold"),
            fg="white",
            bg="black",
            justify="center",
        )
        self.overlay_message_label.pack(
            expand=False, pady=(self.overlay_window.winfo_screenheight() // 4.5, 15)
        )
        self.overlay_time_label = tk.Label(
            self.overlay_window,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_OVERLAY_TIME, "bold"),
            fg="white",
            bg="black",
        )
        self.overlay_time_label.pack(pady=15)
        self.click_to_close_label = tk.Label(
            self.overlay_window,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_OVERLAY_CLICK_PROMPT),
            fg=COLOR_LABEL_MUTED,
            bg="black",
            justify="center",
        )
        self.click_to_close_label.pack(pady=(20, 0))

        def update_overlay_elements(seconds_left):
            if not (self.overlay_window and self.overlay_window.winfo_exists()):
                return
            if seconds_left >= 0:
                mins, secs = divmod(seconds_left, 60)
                self.overlay_time_label.config(text=f"{mins:02d}:{secs:02d}")
                click_message = (
                    "화면을 클릭하면 휴식이 끝나고, 바로 다음 집중 시간이 시작돼요."
                )
                if is_long_rest and seconds_left == 0:
                    self.overlay_message_label.config(
                        text="긴 휴식 끝! 다시 시작할 준비가 되면 화면을 클릭하세요."
                    )
                if self.force_rest_var.get() and not is_long_rest:
                    if seconds_left == 0:
                        self.overlay_message_label.config(
                            text="휴식 끝! 다음 집중을 위해 화면을 클릭해주세요."
                        )
                        self.click_to_close_label.config(text=click_message)
                        self.overlay_window.bind(
                            "<Button-1>", self.close_overlay_and_start_work
                        )
                        self.overlay_window.config(cursor="hand2")
                    else:
                        self.click_to_close_label.config(
                            text="정해진 시간 동안은 화면을 클릭해도 닫히지 않아요."
                        )
                        self.overlay_window.unbind("<Button-1>")
                        self.overlay_window.config(cursor="")
                else:
                    self.click_to_close_label.config(
                        text=(
                            click_message
                            if not (is_long_rest and seconds_left > 0)
                            else "긴 휴식 중... 화면을 클릭하여 종료할 수 있어요."
                        )
                    )
                    self.overlay_window.bind(
                        "<Button-1>", self.close_overlay_and_start_work
                    )
                    self.overlay_window.config(cursor="hand2")
                if self.force_rest_var.get() and not is_long_rest and seconds_left == 0:
                    pass
                elif seconds_left == 0 and not (
                    self.force_rest_var.get() and not is_long_rest
                ):
                    self.close_overlay_and_start_work()
                else:
                    self.overlay_window.after(
                        1000, update_overlay_elements, seconds_left - 1
                    )

        update_overlay_elements(duration_seconds)
        initial_click_prompt = (
            "화면을 클릭하면 휴식이 끝나고, 바로 다음 집중 시간이 시작돼요."
        )
        if is_long_rest:
            initial_click_prompt = "긴 휴식 중... 화면을 클릭하여 종료할 수 있어요."
        if not (self.force_rest_var.get() and not is_long_rest):
            self.click_to_close_label.config(text=initial_click_prompt)
            self.overlay_window.bind("<Button-1>", self.close_overlay_and_start_work)
            self.overlay_window.config(cursor="hand2")
        else:
            self.click_to_close_label.config(
                text="정해진 시간 동안은 화면을 클릭해도 닫히지 않아요."
            )
            self.overlay_window.unbind("<Button-1>")
            self.overlay_window.config(cursor="")

    def check_meal_time_periodically(self):
        now = datetime.datetime.now()
        current_date = now.date()
        if current_date != self.today_date:
            self.today_date = current_date
            self.total_work_seconds_today = 0
            self.pomodoro_cycles_today = 0
            self.update_stats_display()
            for meal in self.meal_alert_shown_today:
                self.meal_alert_shown_today[meal] = False
        if not self.use_meal_alert_var.get():
            self.root.after(MEAL_CHECK_INTERVAL_MS, self.check_meal_time_periodically)
            return
        user_defined_times = {}
        valid_times = True
        for meal_name, time_var in self.meal_times_vars.items():
            time_obj = self.validate_meal_time_format(time_var.get(), meal_name)
            if time_obj is None:
                valid_times = False
                break
            user_defined_times[meal_name] = time_obj
        if not valid_times:
            self.root.after(MEAL_CHECK_INTERVAL_MS, self.check_meal_time_periodically)
            return
        for meal_name, meal_time_obj in user_defined_times.items():
            target_meal_dt = datetime.datetime.combine(current_date, meal_time_obj)
            if (
                target_meal_dt.hour == now.hour
                and target_meal_dt.minute == now.minute
                and not self.meal_alert_shown_today[meal_name]
            ):
                self.show_meal_alert(f"{meal_name} 시간이에요! 🍚 맛있는 식사 하세요!")
                self.meal_alert_shown_today[meal_name] = True
                break
        self.root.after(MEAL_CHECK_INTERVAL_MS, self.check_meal_time_periodically)

    def show_meal_alert(self, message):
        meal_alert_win = tk.Toplevel(self.root)
        meal_alert_win.title("밥 먹을 시간!")
        meal_alert_win.configure(bg=COLOR_BACKGROUND)
        meal_alert_win.attributes("-topmost", True)
        meal_alert_win.attributes("-alpha", 0.95)
        win_width = 330
        win_height = 170
        x = (meal_alert_win.winfo_screenwidth() // 2) - (win_width // 2)
        y = (meal_alert_win.winfo_screenheight() // 3) - (win_height // 2)
        meal_alert_win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        meal_alert_win.resizable(False, False)
        tk.Label(
            meal_alert_win,
            text=message,
            font=(FONT_FAMILY, FONT_SIZE_MEDIUM - 1, "bold"),
            wraplength=win_width - 40,
            justify="center",
            bg=COLOR_BACKGROUND,
            fg=COLOR_TEXT,
        ).pack(expand=True, padx=15, pady=15)
        tk.Button(
            meal_alert_win,
            text="알겠어요!",
            command=meal_alert_win.destroy,
            width=9,
            bg=COLOR_BUTTON,
            fg=COLOR_BUTTON_TEXT,
            activebackground=COLOR_BUTTON_ACTIVE,
            activeforeground=COLOR_BUTTON_TEXT,
            font=(FONT_FAMILY, FONT_SIZE_BUTTON, "bold"),
            relief=tk.FLAT,
            borderwidth=0,
            padx=6,
            pady=3,
        ).pack(pady=(0, 10))
        try:
            import winsound

            winsound.PlaySound(
                "SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC
            )
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    # 창 최소 크기 설정 (선택적) - 내용이 너무 작아져도 유지할 최소 크기
    # root.minsize(360, 480) # 예시: 너비 360, 높이 480
    root.update_idletasks()
    app.adjust_window_size()  # 초기 창 크기 조절
    root.mainloop()
