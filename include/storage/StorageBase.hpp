#pragma once

namespace hedging {

class StorageBase {
public:
    StorageBase(double cap, double eff);
    virtual ~StorageBase() = default;

    virtual void step(double power_mw, double dt_hours);

    double soc() const noexcept { return m_soc; }

protected:
    double m_capacity;
    double m_eff;
    double m_soc;
};

}
