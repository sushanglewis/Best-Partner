import React from "react";
import { Container, Text } from "@nextui-org/react";
import { personalInfo } from "../data/config";

const FooterBar = () => {
  return (
    <footer className="bg-[#F3EFFF] py-4 mt-8 border-t border-[#E0E0E0]">
      <Container lg className="max-w-4xl mx-auto">
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
          <Text size="sm" color="foreground-500">
            姓名：{personalInfo.name} | 出生年月：{personalInfo.birth} | 年龄：
            {personalInfo.age}
          </Text>
          <Text size="sm" color="foreground-500">
            电话：{personalInfo.phone} | 邮箱：{personalInfo.email} | 地址：
            {personalInfo.address}
          </Text>
        </div>
      </Container>
    </footer>
  );
};

export default FooterBar;
