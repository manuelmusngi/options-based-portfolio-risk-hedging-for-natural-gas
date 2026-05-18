#pragma once

#include <vector>
#include <memory>
#include "storage/StorageBase.hpp"

namespace hedging {

class StorageController {
public:
    explicit StorageController(std::unique_ptr<StorageBase> storage);

    // Decide power (MW) given current price and simple thresholds
    double decide_power(double price,
                        double low_threshold,
                        double high_threshold) const;

    void step(double power_mw, double dt_hours);

    [[nodiscard]] double soc() const noexcept;

private:
    std::unique_ptr<StorageBase> m_storage;
};

} // namespace hedging
