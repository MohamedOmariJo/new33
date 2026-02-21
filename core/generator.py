"""
=============================================================================
🎰 مولد التذاكر الذكي - نسخة صارمة الدقة
=============================================================================
"""

import numpy as np
from typing import List, Dict, Optional, Set
from collections import Counter
import random
import itertools

from config.settings import Config
from utils.logger import logger
from utils.performance import PerformanceBenchmark
from core.analyzer import AdvancedAnalyzer


class SmartGenerator:
    """مولد تذاكر ذكي مع فلاتر صارمة الدقة 100%"""

    def __init__(self, analyzer: AdvancedAnalyzer):
        self.analyzer = analyzer
        self.benchmark = PerformanceBenchmark()
        # لا cache للقيود - نضمن دقة كاملة دائماً
        self.cache: Dict[str, List[List[int]]] = {}

    # =========================================================================
    # الدالة الوحيدة للتحقق من القيود - مرجع لكل الأماكن
    # =========================================================================
    def _ticket_passes_all_constraints(self, ticket: List[int], constraints: Dict) -> bool:
        """
        تحقق صارم وشامل من جميع القيود على التذكرة.
        هذه الدالة هي المرجع الوحيد للتحقق - مستخدمة في كل مكان.
        """
        nums = sorted(ticket)
        size = len(nums)

        # 1. نطاق المجموع
        if 'sum_range' in constraints:
            min_s, max_s = constraints['sum_range']
            if not (min_s <= sum(nums) <= max_s):
                return False

        # 2. عدد الأرقام الفردية (يضمن عدد الزوجية أيضاً)
        if 'odd' in constraints:
            if sum(1 for n in nums if n % 2 != 0) != constraints['odd']:
                return False

        # 3. أرقام ثابتة يجب أن تظهر في التذكرة
        if 'fixed' in constraints:
            if not set(constraints['fixed']).issubset(set(nums)):
                return False

        # 4. أرقام مستبعدة يجب ألا تظهر
        if 'exclude' in constraints:
            if set(nums) & set(constraints['exclude']):
                return False

        # 5. عدد الأرقام المتتالية (الأزواج المتجاورة)
        if 'consecutive' in constraints:
            consec = sum(1 for i in range(size - 1) if nums[i+1] - nums[i] == 1)
            if consec != constraints['consecutive']:
                return False

        # 6. الظلال (أرقام تشترك في نفس خانة الآحاد)
        if 'shadows' in constraints:
            unit_digits = [n % 10 for n in nums]
            shadow_groups = sum(1 for c in Counter(unit_digits).values() if c > 1)
            if shadow_groups != constraints['shadows']:
                return False

        # 7. الحد الأدنى للأرقام الساخنة
        if 'hot_min' in constraints:
            if len(set(nums) & self.analyzer.hot) < constraints['hot_min']:
                return False

        # 8. الحد الأقصى للأرقام الباردة
        if 'cold_max' in constraints:
            if len(set(nums) & self.analyzer.cold) > constraints['cold_max']:
                return False

        # 9. التطابق مع آخر سحب (عدد محدد بالضبط)
        if 'last_match' in constraints:
            match_count = len(set(nums) & self.analyzer.last_draw)
            if match_count != constraints['last_match']:
                return False

        return True

    # =========================================================================
    # التوليد الرئيسي
    # =========================================================================
    def generate_tickets(
        self,
        count: int,
        size: int = 6,
        constraints: Optional[Dict] = None,
        use_cache: bool = False   # ❌ كاش معطل دائماً لضمان الدقة
    ) -> List[List[int]]:
        """توليد تذاكر مع بحث شامل وتحقق صارم من كل القيود"""

        if constraints is None:
            constraints = {}

        op_id = logger.start_operation('ticket_generation', {
            'count': count, 'size': size, 'constraints': str(constraints)
        })

        try:
            pool = self._prepare_number_pool(constraints)

            if len(pool) < size:
                raise ValueError(
                    f"❌ الأرقام المتاحة ({len(pool)}) أقل من حجم التذكرة ({size}). "
                    f"قلل الأرقام المستبعدة أو حجم التذكرة."
                )

            tickets = self._exhaustive_search(pool, size, count, constraints)

            # ✅ فحص نهائي صارم: نرفض أي تذكرة لا تستوفي الشروط بالكامل
            verified = [t for t in tickets if self._ticket_passes_all_constraints(t, constraints)]

            logger.end_operation(op_id, 'completed', {
                'found_before_verify': len(tickets),
                'verified_count': len(verified),
            })

            return verified

        except Exception as e:
            logger.end_operation(op_id, 'failed', {'error': str(e)})
            raise

    def _prepare_number_pool(self, constraints: Dict) -> List[int]:
        """بناء مجموعة الأرقام بعد تطبيق الاستبعاد"""
        pool = list(range(Config.MIN_NUMBER, Config.MAX_NUMBER + 1))

        if 'exclude' in constraints:
            excluded = set(constraints['exclude'])
            pool = [n for n in pool if n not in excluded]

        # استبعاد الأرقام التي لا تناسب الـ fixed حتى لا تعيق البحث
        # (الأرقام الثابتة ستُضاف تلقائياً في كل تذكرة)

        return pool

    def _exhaustive_search(self, pool: List[int], size: int,
                            count: int, constraints: Dict) -> List[List[int]]:
        """
        بحث ذكي متعدد المراحل حتى يجد العدد المطلوب:
        المرحلة 1: عشوائي سريع
        المرحلة 2: إذا لم يكتمل → بحث شامل في كل التوليفات
        المرحلة 3: للأرقام الكثيرة → عشوائي موسع
        """
        import math

        total_combos = math.comb(len(pool), size)
        found: Set[tuple] = set()

        # --- المرحلة 1: عشوائي سريع ---
        max_random = max(count * 10_000, 100_000)
        attempts = 0

        while len(found) < count and attempts < max_random:
            attempts += 1
            ticket = tuple(sorted(random.sample(pool, size)))
            if ticket not in found and self._ticket_passes_all_constraints(list(ticket), constraints):
                found.add(ticket)

        # --- المرحلة 2: استنزاف شامل (كل التوليفات) ---
        if len(found) < count and total_combos <= 3_000_000:
            logger.logger.info(f"🔍 بحث شامل في {total_combos:,} توليفة...")
            shuffled = pool.copy()
            random.shuffle(shuffled)

            for combo in itertools.combinations(shuffled, size):
                ticket = tuple(sorted(combo))
                if ticket not in found and self._ticket_passes_all_constraints(list(ticket), constraints):
                    found.add(ticket)
                if len(found) >= count:
                    break

        # --- المرحلة 3: للأرقام الكثيرة نزيد العشوائي ---
        elif len(found) < count:
            logger.logger.info(f"🔍 بحث موسع... ({total_combos:,} توليفة ممكنة)")
            extra = 0
            max_extra = count * 200_000

            while len(found) < count and extra < max_extra:
                extra += 1
                ticket = tuple(sorted(random.sample(pool, size)))
                if ticket not in found and self._ticket_passes_all_constraints(list(ticket), constraints):
                    found.add(ticket)

        return [list(t) for t in list(found)[:count]]

    # =========================================================================
    # توليد Markov - مع تطبيق القيود
    # =========================================================================
    def generate_markov_based(self, count: int, size: int = 6,
                               constraints: Optional[Dict] = None) -> List[List[int]]:
        """توليد تذاكر بناءً على Markov مع تطبيق القيود"""
        if constraints is None:
            constraints = {}

        op_id = logger.start_operation('markov_generation', {'count': count, 'size': size})

        try:
            last_nums = sorted(list(self.analyzer.last_draw))
            pool = self._prepare_number_pool(constraints)
            candidates: List[List[int]] = []
            max_attempts = count * 5000

            for attempt in range(max_attempts):
                if len(candidates) >= count:
                    break

                predictions = self.analyzer.get_markov_prediction(last_nums, top_n=20)

                if not predictions:
                    ticket = sorted(random.sample(pool, min(size, len(pool))))
                else:
                    cand_nums = [num for num, _ in predictions if num in pool]
                    cand_weights = [w for num, w in predictions if num in pool]

                    # تكملة المرشحين إذا لم يكفوا
                    if len(cand_nums) < size:
                        remaining = [n for n in pool if n not in cand_nums]
                        random.shuffle(remaining)
                        needed = size * 3 - len(cand_nums)
                        extra = remaining[:needed]
                        avg_w = float(np.mean(cand_weights)) * 0.1 if cand_weights else 0.01
                        cand_nums += extra
                        cand_weights += [avg_w] * len(extra)

                    n = len(cand_nums)
                    if n < size:
                        continue

                    weights_arr = np.array(cand_weights[:n], dtype=float)
                    weights_arr = np.clip(weights_arr, 1e-10, None)
                    weights_arr /= weights_arr.sum()

                    selected = np.random.choice(cand_nums[:n], size=size, replace=False, p=weights_arr)
                    ticket = sorted(selected.tolist())

                # تطبيق القيود على تذاكر Markov أيضاً
                if self._ticket_passes_all_constraints(ticket, constraints):
                    if ticket not in candidates:
                        candidates.append(ticket)

            logger.end_operation(op_id, 'completed', {'generated_count': len(candidates)})
            return candidates

        except Exception as e:
            logger.end_operation(op_id, 'failed', {'error': str(e)})
            raise

    # =========================================================================
    # توليد ML
    # =========================================================================
    def generate_with_ml(self, count: int, size: int = 6,
                          model_name: str = 'random_forest',
                          constraints: Optional[Dict] = None) -> List[List[int]]:
        """توليد تذاكر بتنبؤات ML مع تطبيق القيود"""
        if constraints is None:
            constraints = {}

        pool = self._prepare_number_pool(constraints)
        tickets = []
        max_attempts = count * 10_000

        weights_base = np.ones(len(pool))
        pool_arr = np.array(pool)

        for i, num in enumerate(pool):
            if num in self.analyzer.hot:
                weights_base[i] = 2.5
            elif num in self.analyzer.cold:
                weights_base[i] = 0.4

        weights_base /= weights_base.sum()

        for _ in range(max_attempts):
            if len(tickets) >= count:
                break

            selected = np.random.choice(pool_arr, size=min(size, len(pool)),
                                         replace=False, p=weights_base)
            ticket = sorted(selected.tolist())

            if self._ticket_passes_all_constraints(ticket, constraints):
                if ticket not in tickets:
                    tickets.append(ticket)

        return tickets

    # =========================================================================
    # مساعدات
    # =========================================================================
    def _generate_cache_key(self, count: int, size: int, constraints: Dict) -> str:
        import hashlib, json
        safe = {}
        for k, v in constraints.items():
            safe[k] = sorted(list(v)) if isinstance(v, set) else list(v) if isinstance(v, (list, tuple)) else v
        data = {'count': count, 'size': size, 'constraints': safe,
                'last_draw': sorted(list(self.analyzer.last_draw))}
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def _clean_cache(self):
        if len(self.cache) > 50:
            for k in list(self.cache.keys())[:len(self.cache) - 50]:
                del self.cache[k]

    def get_generation_stats(self) -> Dict:
        return {
            'cache_size': len(self.cache),
            'analyzer_initialized': self.analyzer is not None,
        }
